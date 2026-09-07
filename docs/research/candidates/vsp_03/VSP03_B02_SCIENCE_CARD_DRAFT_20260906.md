Learning when to submit into a shared service slot may improve team return over a fixed readiness scheduler; event-rule initialization may or may not help that learning.
Binding structure: temporal abstraction / termination, fixed N=2; one agent's submission removes its partner's service opportunities.

# VSP03 B02 draft — shared-service termination

**PROPOSED B/EXPLORE, awaiting direction selection; this is not a frozen card or launch authorization.**
The recommendation is to open this coupled family through `em:vsp_03:convergence`.
The accepted N1 update-128 comparison remains paused: no unchanged seeds, tuning or updates.
No new experiment, learner construction or calibration was performed for this proposal.

## Decision and existing evidence

Can a learned termination policy improve native team return over a fixed public readiness-and-yield
scheduler when submission occupies the only service slot? The primary comparison is T minus R at
the final budget. A same-information generic learner G is the containing null: report T-G and G-R
alongside T-R, so ordinary learning is not credited to the event initialization.

The B01 Convergence intake's **“Decisions this intake produces”** allows a reasoned coupled
proposal when continuation/submission changes partner feasibility, resources or native payoff.
Its complete response selected no successor. B01's primary T=G=F in three pairs is strong contrary
evidence to more unchanged initialization training. Its update-32 T-G gains in all three pairs
remain local support for a useful prior, weakened by G's then-non-submitting greedy evaluation
and absent early F measurement. No observed-positive checkpoint is promoted here.

The claim ceiling is a local learning/comparison observation on this new synthetic N2 host and
the declared budget. It is not stable superiority, a unique causal mechanism, a MARL-versus-N1
effect estimate, transfer, deployment, optimality, or authentication of the old event source.
The new shared resource makes the task coupled; only a suitable later intervention could attribute
a performance difference specifically to coupling. FSD's stopped fixed-K2 family is unchanged.

## Proposed host and native consequence

Reuse the B01 departure/re-entry law, 40 primitive transitions, and eight-tick irreversible service.
There are two fixed controller/target identities, one pending job per controller, and one common
service slot. No agent joins, leaves, is replaced or rejoins; target re-entry is not roster change.

- Both targets start occupied with dwell age zero. Each has an independent exogenous tape: occupied
  departure probability `1/(d+4)`, absent re-entry probability `1/2`; dwell updates as in B01.
  Both complete target trajectories advance through all 40 ticks, including after job completion.
- One controller has opportunities at `0,4,...,32`, the other at `2,6,...,30`. A public fair bit
  assigns these phases to identities once per episode, paired across arms. N remains two.
  The phase change is a declared new-host assumption, not a modification of B01.
- At its opportunity, a pending controller chooses CONTINUE or SUBMIT only when the slot is free.
  SUBMIT starts service immediately and occupies the slot for the next eight transitions, including
  after a failed service sample. Completion at `t+8` releases the slot before that time's decision.
  There is no queue, cancellation, second attempt, collision lottery or other task-assignment learner.
- A busy slot forces waiting: no sampled action, log-probability or gradient row is inserted.
  The other controller can act at its next own free opportunity. A voluntary CONTINUE does not
  reserve the slot: its partner can take it two ticks later. Pending jobs without an accepted
  submission by their last opportunity expire at t=40. Already submitted service completes normally.
- A job succeeds iff all states `t+1,...,t+8` are occupied. Each job contributes integer units
  `200*success - 10*attempt - waiting_ticks`; waiting counts its pending primitive ticks before
  submission, or all 40 when never submitted. Team return is the sum of both jobs' units divided
  by 400. No rule-agreement reward or reward per decision is introduced.

For example, a submission at t=26 occupies the slot until t=34 and prevents a pending phase-zero
partner from submitting at t=28 or its last chance t=32. CONTINUE at t=26 leaves that partner's
t=28 action feasible. This is a consequence of the proposed law, not a simulated result or proof
that either action is better. Scarce capacity, uncertain persistence and the deadline determine
whether surrendering the current opportunity improves team utility.

## Information, learner and comparators

Every primitive target event is public to both arms and controllers. Each target has its own B01
`a,e,b` processor. At that target's controller clock, read before update; an actual or forced
CONTINUE sets `a=y,e=0`. Primitive departure while armed latches e through re-entry. SUBMIT clears
that target's bits. These updates also occur at forced-wait clock points; eligibility and actual
decision-row counts are recorded separately. No future tape or realized service success is input.

At an eligible decision both T and G receive the same 14 features: `t/40`; own `(y,d/40,a,e,b)`;
partner `(y,d/40,a,e,b)`; partner-pending bit; own phase bit; and the partner's next scheduled
opportunity time divided by 40, using 1 when no opportunity remains. Partner pending does not mean
it can still submit: its known clock/deadline also matters. The slot is necessarily free at every
sampled decision. Identity is retained by environment state; the actor uses this own/partner view.

Each arm has one actor `14->32->32->1` with tanh hidden layers and a trainable direct-own-b
coefficient, and one critic `14->32->1`; parameters are shared by the two controllers within
that arm. T/G are separately trained with corresponding random hidden/critic weights paired.
As in B01, output weights start at zero: G's output bias/direct-b start at zero; T's start at
`-log(3)` and `2*log(3)`. Both can learn every coefficient. There is no permanent veto, action
constraint, distinct policy class or extra information for T. Both partners co-adapt under their
arm's shared parameters; controllers and episode evaluations are not independent training seeds.

R is a fixed, same-information readiness-and-yield reference with no fit or search. At a free own
opportunity, submit iff own b=1, except yield when the partner is pending, has a remaining future
opportunity, currently has b=1, and has strictly greater current dwell age. Ties submit now.
Greater occupied dwell age means lower next-tick departure hazard under the declared law. R uses
this public ranking without a future rollout, optimal scheduler or privileged prediction. It is
a credible resource-aware null, not a tuned baseline or upper. The strongest alternative is that
R or ordinary G already handles the scheduling question and the event prior adds no value.

Reuse B01's complete-episode actor-critic, Adam 1e-3, float32 CPU, entropy schedule and one joint
backward/optimizer step per batch. Use primitive gamma=1 and terminal bootstrap zero. Average the
sum of both controllers' valid policy-gradient rows over complete joint episodes; critic loss
uses valid rows. Do not normalize the actor by policy-dependent decision count or add forced
actions as samples. Return-to-go is the actual remaining **team** reward from each decision time.
In particular, B01's `(terminal_units + decision_time)/200` shortcut is not valid for two pending
jobs: record/subtract the actual sunk team reward or use its actual reward timeline.

## Budget, observable and exposure

Proposed first observation: one paired training seed, seed 4; two learner arms, each 128 Adam
updates on batches of 128 complete joint episodes. The final update 128 is chosen as the inherited
working learner budget on a changed host, not a short deployment budget or selected early checkpoint.
There are no added training seeds or tuning configurations in this proposal.

Evaluate each final learner on 1,024 greedy episodes (zero logit chooses CONTINUE), and on 1,024
stochastic episodes using a separately declared evaluation action stream. Greedy native team mean
return is primary; stochastic native return is a prespecified secondary reading of policy behavior.
R uses the same 1,024 exogenous evaluation episode identities. No intermediate checkpoint evaluation
or best-checkpoint selection is needed. Preserve every arm, its batch return curve, final weights,
actual interactions/gradient rows, success/attempt/miss counts, and final primary/secondary outputs.
Environment streams are addressed by seed/split/episode/target/tick, independent of policy actions;
training and evaluation splits are disjoint. CM fixes exact stream constants before launch.

`VSP03_B02_COUNTS_20260906.json` gives machine-computed counts and historical exposure, without
constructing a model: 2,083 parameters per arm; 16,384 training joint episodes and 655,360 team ticks
per arm; at most 278,528 valid training rows per arm. The algorithm totals 37,888 joint episodes,
1,515,520 team ticks, 3,031,040 target transitions and 256 optimizer steps, including evaluation/R.
A single focused eight-episode check would add 320 team ticks, 640 target transitions and zero
learning. No nested candidate, policy, trajectory, solver or support search is proposed.

The exposure line uses B01's actual six displacement/initial-norm ratios, 0.3998–0.5213 after 128
steps at this learning rate, and the proposed nonzero learner budget. They show that the reused
learning recipe moved on N1; they do not measure N2 displacement. CM records actual N2 initial,
first-update and final norms with the accepted learner path. `128*1e-3=0.128` is a nominal scale,
not an Adam displacement bound. This consultation adds zero new learner or environment exposure.

The dominant work is two arms × 128 updates × 128 joint episodes × 40 ticks, with two target
updates per tick and at most 17 actor opportunities per episode, versus nine in N1. Network
widths stay 32; inputs expand 6 to 14. Counts separate target transitions from team time and
training from evaluation. Prior complete N1 pairs took 2.365–5.905 seconds. A conditional planning
allowance of four times the largest observed pair is 23.620 seconds for the proposed pair, not
a measured N2 time or bound; actual unit cost is unknown. The whole new logical invocation has
a proposed **120-second wall cap**, including both learners, evaluations, focused check and
publication. There is no extra calibration invocation, automatic relaunch or residual B01 budget.

Portable execution would use the configured remote-first CPU route with one compute thread, a committed exact launch
source, detached supervisor and fresh remote memory admission. Existing monitoring applies only
after an accepted run handle. On timeout or dependent missing output, retain partial facts and
return to CM/DM; do not call it a completed primary comparison or alter the budget silently.

## Interpretation, prediction and implementation scope

MEI is 0.02 team-return units: one four-tick waiting interval for each job, on the per-job-normalized
scale. Tuned headroom is absent on this new host; the N1 baseline cannot be reused as a matched
result because population, clock, feasibility, reward aggregation, input width and exposure differ.
Its implementation, training recipe and cost evidence are reusable. R is measured in this B and
does not create tuned headroom. Missing headroom or an exact upper is no precondition.

Above-MEI T-R would support a bounded one/two-new-seed follow-up if the primary comparison is
trustworthy; T-G says whether the initialization contributed. Inside-MEI differences suggest a
small/local effect; equality or an adverse T-R weakens this proposed learned scheduler at this
budget. G-R positive with no T-G advantage supports ordinary learned scheduling, not the prior.
T-G positive while T<=R remains only an initialization signal against G. Any greedy gain and
stochastic/native loss are reported separately. No seed must improve, and a single pair cannot
estimate training-population uncertainty or justify stable superiority.

DM prediction: final T-G is likely small, given all three prior primary zeros and the public
Markov state. Whether either learner beats R is unresolved; partner opportunities make fixed
local readiness insufficient as a complete decision principle, but do not prove a gain exists.
Owner prediction: not taken; a ladder prediction item follows only if a card is actually frozen.

This object needs **none** of ENGINEERING_SCOPE_SPEC §4's optional machinery. It reuses the
project's existing remote execution and observation route and adds no new scheduler/monitor.
No code has been commissioned. If selected, a CM owns a separate `vsp03_b02` module, thin runner
and focused tests, preserves B01, and reuses its collector/learner/publication patterns where
semantically valid. One focused check covers service exclusion/release, partner deadline loss,
causal observations, valid actor rows and team reward-to-go; no exhaustive A precedes this B.
The ordinary 2,000-new-line/600-runner-line limits apply; no exception is requested.

## Source checks that changed this proposal

Question searched: how do temporally extended decisions affect another agent's actions/credit,
and is termination learning already a generic alternative? The local Inst-sci catalog snapshot
contains 190 real records. Title/abstract/keyword queries found zero termination/option-critic
matches, six macro-action/asynchrony matches and two resource/scheduling matches. This is bounded
coverage, not a novelty search result. My-lib's existing SQLite index points to its 2026-07-26
fixture registry (two indexed mechanism records); no real collection was verified through that entry point, and synthetic records
were excluded. No download, library rebuilding or service was added.

- Jung et al., *Agent-Centric Actor-Critic for Asynchronous Multi-Agent Reinforcement Learning*,
  ICML 2025, [official paper](https://proceedings.mlr.press/v267/jung25a.html).
  Local `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0449.json`, PDF p.2, elements 388–390,
  describes agent-dependent completion times and misleading padded observations. It motivates
  own opportunity clocks and valid decision rows here. It does not require ACAC, PPO or attention
  for this small fully public host and supplies no result for our initialization.
- Liang et al., *Asynchronous Credit Assignment for Multi-Agent Reinforcement Learning*, IJCAI
  2025, [official paper](https://www.ijcai.org/proceedings/2025/20).
  Local `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0530.json`, PDF p.2, elements 132–133,
  identifies dependencies on actions still executing. It changes the design from independent
  N1 copies to occupied shared capacity and actual remaining team reward. Its VSP abbreviation
  is not evidence of identity with VSP-03; no value-decomposition method or claim is imported.
- Bacon, Harb and Precup, *The Option-Critic Architecture*, arXiv:1609.05140v2 / AAAI 2017,
  [primary version](https://arxiv.org/abs/1609.05140v2), abstract, closes the local catalog gap:
  generic RL can learn termination without added rewards/subgoals. Thus G shares all information
  and the trainable policy class; the proposal does not call termination learning itself novel.

These are source-supported design considerations. The shared-slot law, R and the proposed effect
remain DM design/inference. Current evidence-spec §§4, 5.2, 11.4, 11.7–11.9 control the question;
an exact optimum, exhaustive cause or paid headroom experiment would add no needed decision here.
Owner review scan at this preparation boundary: `item.py reviews --json` returned `[]`.
