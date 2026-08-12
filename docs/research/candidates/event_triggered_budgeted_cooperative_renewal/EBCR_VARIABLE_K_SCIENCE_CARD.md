# Event-Triggered Budgeted Cooperative Renewal B1 science card

Owner: `direction:variable-k-cooperative-renewal` Explorer Manager  
Candidate: `CAND-EVENT-TRIGGERED-BUDGETED-COOPERATIVE-RENEWAL`  
Treatment: `EBCR-B1-VARIABLE-K-COOPERATIVE-RENEWAL-v1`

This is a prospective construct-first toy experiment for the project objective.
It asks whether one shared MARL policy can vary skill period `k` online and
improve either robustness or performance. It does not require an existing host,
runner, skill lifecycle hook, or UAV adapter; CM owns those construction facts.

## Question and project value

In a two-agent tracking--relay task whose useful skill lifetime changes across
unobserved regimes, can a learned bounded local renewal hazard (`LOCAL`) beat a
validation-selected fixed-`k` policy after duration/noise shift? On top of that
local mechanism, can four bits per physical tick--one invalidation and one
readiness bit from each agent--coordinate renewals (`COORD`) well enough to
improve return or worst-condition robustness without increasing the physical,
interaction, inference, communication, or renewal budget?

The treatment is one policy parameterization trained once across duration
regimes. It is not a collection of separately trained policies indexed by `k`.
Its realized skill period is the interval between successive renewal events and
may differ by agent, episode, and phase. Either of these results is project-
valuable:

1. `LOCAL` or `COORD` beats the fixed-`k` baseline on shifted-condition
   robustness; or
2. `LOCAL` or `COORD` beats it on mean task performance at the same caps.

The extra coordination mechanism is valuable only if `COORD` also separates
from `LOCAL` and from schedule controls that preserve renewal count and period
distribution while destroying event alignment.

## Exact toy: switching-tempo cooperative tracking--relay

An episode lasts exactly `H=128` physical ticks and contains two agents:

- tracker `T`, whose current binary skill `s_T` selects one of two target-motion
  tracking controllers; and
- relay `R`, whose current binary skill `s_R` selects one of two relay/channel
  controllers.

The environment has two latent binary requirements `(z_T,z_R)`. Initial values
are independent fair bits. Piecewise-constant phases have lengths drawn from
the split-specific distributions below. At each phase boundary:

- with `joint_mismatch=ON`, both latent requirements flip;
- with `joint_mismatch=OFF`, exactly one uniformly selected requirement flips.

The schedule and all exogenous draws are independent of every arm's actions and
are paired across arms. There is no observable phase label, phase age, next
boundary, duration distribution label, or mismatch-mode label.

At each physical tick, agent `i` observes

`o_i(t) = z_i(t) XOR Bernoulli(p_obs)`.

It retains the last three local observations. Renewing instantiates the new
skill as their majority value; a seed-fixed tie rule is included only for an
incomplete prehistory. Three paired pre-roll observations initialize each
skill before tick zero and do not contribute reward or training transitions.
Skill content is therefore fixed and common to every arm; the learned object is
when to renew, not a different low-level controller or skill decoder.

Each agent also observes one local renewal-safety margin. For `T` this is a
geometry margin and for `R` a link margin. The visible value is `+1` when ready
and `-1` otherwise. Each readiness process is a paired two-state Markov chain
with

`P(ready_{t+1}=1 | ready_t=1)=0.90` and
`P(ready_{t+1}=1 | ready_t=0)=0.50`,

initialized from its stationary distribution and independent across agents.
These margins affect renewal timing and cost but not latent task changes or
observation noise.

The within-tick order is fixed: apply any phase change and readiness transition;
draw and expose local observations and any safety event; sample hazard requests;
apply the coordination rule and all forced renewals; instantiate renewed skills;
then compute packet success and reward. Thus a policy may respond to the current
innovation, but a renewal always consumes the current task tick.

If neither agent renews on tick `t`, a task packet succeeds exactly when
`s_T(t)=z_T(t)` and `s_R(t)=z_R(t)`. Any renewal occupies that agent's high-level
interface for the tick; because both roles are required, a packet cannot
succeed on a tick containing any renewal. A simultaneous two-agent renewal
therefore loses one packet tick, whereas two asynchronous renewals lose two.
The per-tick reward is

`r_t = packet_success_t - 0.02 * number_renewed_t
       - 0.10 * number_of_nonready_normal_renewals_t`.

The episode return is `J = (sum_t r_t)/128`. There is no discount in the
reported task estimand. The reward, current latent requirements, phase
schedule, other agent's raw observation, and future margins are never actor
inputs.

## Skill-age, safety envelope, and renewal budget

Skill age is ticks since the latest renewal. All adaptive arms use
`k_min=4` and `k_max=32`:

- an ordinary learned request before age four cannot renew;
- an agent at age 32 renews locally on that tick, irrespective of its partner;
- an injected safety event renews only the affected agent immediately,
  irrespective of age, readiness, pending coordination, or partner state.

The safety event is a host-visible emergency bit, not inferred from the latent
phase. It is absent from the primary task panel. A separate safety panel places
exactly one event, balanced across agent and ticks `32..95`, in every episode.
The event must never wait for a pair renewal. It resets only the affected
agent's age and skill, so later periodic or forced renewals are scheduled from
that new time.

Each agent has at most 31 ordinary renewals plus one reserved emergency renewal
per episode, hence a hard cap of 32 total renewals. The cap admits the most
frequent fixed comparator (`k=4`). Max-age renewal consumes an ordinary token.
The registered generator must show that every arm respects the cap. A missing
emergency renewal, a pair-forced emergency renewal of the unaffected agent, or
a cap violation makes the safety claim and the complete run non-identifying;
it is not a negative result about variable `k`.

## Learned hazard and the two mechanisms

At every non-forced tick, a parameter-shared actor is evaluated once for each
agent. Its local feature vector is:

1. role one-hot (`T` or `R`);
2. skill age divided by 32;
3. current three-sample disagreement rate with the active skill;
4. the signed local geometry/link margin;
5. normalized task time `t/127`;
6. ordinary-renewal budget remaining divided by 31;
7. pending-request age divided by two; and
8. two input slots for the partner's previous-tick invalidation/readiness bits.

The actor is a two-hidden-layer MLP, widths `(32,32)`, `tanh` activations, and
one Bernoulli hazard logit. The two partner slots are present in both learned
arms. They are zero-masked in `LOCAL` and contain the one-tick-delayed partner
summary in `COORD`; all other architecture, initialization, optimizer,
rollouts, actor calls, and action support are identical. A sampled hazard one
is the agent's invalidation request `I_i`; the current readiness bit is `R_i`.
Each agent broadcasts `(I_i,R_i)` every tick in every arm, including controls.
Thus every arm uses exactly two transmitted bits per agent per tick; arms that
do not use the partner channel mask the received bits.

`LOCAL` implements mechanism A. An eligible request renews that agent on the
first tick on which its own readiness is one. A request may remain pending for
at most two ticks; on expiry it renews locally even if the readiness margin is
negative. Safety and max-age renewals bypass this rule.

`COORD` implements mechanism B. Eligible invalidation requests are retained for
the same two-tick window. If both agents have live requests and both are ready,
both renew on that tick. If a request remains solitary until its window expires,
only its owner renews under the `LOCAL` rule. Safety and max-age renewals are
always single-agent events and never wait for or manufacture a partner request.
The coordinator has no raw observation, hazard probability, continuous margin,
latent state, or future information--only the four current summary bits and the
bounded pending state.

The high-level skill interface is evaluated at a fixed physical frequency of
one call per tick in all arms. Low-level task evolution also remains one tick
per step; choosing a longer `k` never skips physics or interactions.

## Hazard credit and fixed learner

`LOCAL` and `COORD` are trained separately but from paired initial parameters
and paired exogenous trajectories with parameter-sharing across the two roles.
They use multi-agent PPO with a centralized training-only critic. The critic
may see `(z_T,z_R)`, both local observations, skills, ages, readiness values,
pending states, current ordinary budget, and task time, but neither a future
phase boundary nor a split/distribution identity. It is discarded at test.
It is a two-hidden-layer `(64,64)` `tanh` MLP with one scalar value output.

Use `gamma=0.99`, GAE `lambda=0.95`, PPO clip `0.20`, Adam learning rate
`3e-4`, value coefficient `0.5`, entropy coefficient `0.01`, gradient-norm cap
`1.0`, four epochs per collected batch, and minibatches of 1,024 tick records.
Each learned arm receives exactly 512 complete training episodes per base seed;
there is no early stopping, checkpoint selection, restart, sweep, rescue, or
arm-specific tuning. The final optimizer state is the only evaluated learned
checkpoint.

An ordinary Bernoulli request contributes its log probability and GAE
advantage at the tick where it was sampled, including when its eventual renewal
is joined or delayed inside the two-tick window. Both agents' request records
remain in the joint trajectory, allowing downstream joint reward to credit both
hazards. Host-forced safety and max-age renewals have no actor log probability
and are masked from the policy loss while remaining in critic returns. Report
request rates, executed renewal rates, pending delays, hazard entropy, actor and
critic losses, and forced-event counts by role and phase cell. This separates a
low-return policy from a hazard that never received usable credit.

## Training, selection, and held-out tempo/noise panels

Training phases draw duration uniformly from `{12,20,28}`; observation noise is
`p_obs=0.05`; `joint_mismatch` is balanced ON/OFF. The full 128-tick episode is
always retained, including the final truncated phase. Training contains no
distribution label in either actor or critic and contains no injected safety
event; safety is a host override rather than a learned action.

The four fixed comparators use `k in {4,8,16,32}` and renew each agent when its
age equals `k`, except that the common single-agent safety override resets its
clock. A separate validation panel uses durations `{10,16,24,40}`, noise
`0.10`, and balanced mismatch mode. Exactly one `FIXED-BEST` value is selected
by highest mean validation return over independent selection seeds
`[1009,1013]`, using 32 episodes for each of the eight duration-by-mismatch
cells; a tie selects the larger `k`. That value is frozen before the
conclusion panel. All four fixed-grid results and the test-cell hindsight grid
envelope are reported, but the hindsight envelope is diagnostic rather than a
deployable selected baseline.

The held-out conclusion panel crosses `joint_mismatch in {OFF,ON}` with four
tempo/noise cells:

| Cell | Phase-duration support | `p_obs` | Purpose |
|---|---|---:|---|
| `ID` | `{12,20,28}` | `0.05` | training-distribution performance |
| `SHORT` | `{6,8,10}` | `0.10` | faster-than-trained changes |
| `LONG` | `{36,44,52}` | `0.10` | slower-than-trained changes |
| `MIXED_NOISY` | `{6,16,32,52}` | `0.20` | duration mixture plus cue degradation |

There are 64 paired primary episodes per base seed and cell. Every duration
support value, initial latent pair, changing-agent identity in OFF mode,
readiness process, noise draw namespace, and terminal truncation position is
balanced within the panel. The separate safety panel adds 32 paired episodes
per seed and arm, balanced over the same eight cells, with exactly one injected
emergency each.

## Comparators and event-timing controls

The registered result contains:

- `FIXED-4`, `FIXED-8`, `FIXED-16`, `FIXED-32`, and frozen `FIXED-BEST`;
- learned `LOCAL` (mechanism A);
- learned `COORD` (mechanism B);
- `COORD-SHUFFLE`, an evaluation replay that uses, for each agent and paired
  episode, the exact number and multiset of non-forced inter-renewal periods
  generated by `COORD` but permutes those periods with a seed-fixed permutation;
- `COORD-YOKED`, which applies the complete non-forced renewal schedule from a
  different episode in the same `(seed,cell,mode,renewal-count)` stratum;
- `STAGE-ORACLE`, which sees phase boundaries and current readiness solely to
  choose timing, uses the same three-observation majority skill instantiation,
  renews both agents at the first jointly ready tick after a joint change, and
  renews only the changed agent at its first ready tick after an independent
  change. It obeys the same `k_min`, `k_max`, renewal cap, safety override, and
  one-tick renewal cost; it chooses the earliest legal event under those rules.

The exogenous host is replayable because its latent schedule, observations,
margins, and safety events do not depend on actions. In SHUFFLE and YOKED,
renewal content is recomputed from the destination episode's own last three
observations; only timing is transferred. Forced max-age and safety events
remain host-local. If an exact schedule cannot satisfy `k_min`, `k_max`, the
renewal count, and the period multiset simultaneously, that episode is marked
control-ineligible before analysis rather than silently repaired; the primary
timing claim requires at least 90% eligibility in every cell.

All evaluation arms run the same 128 physical ticks, receive the same paired
exogenous episode, execute two actor-sized forward calls per tick (dummy calls
where a policy output is ignored), transmit four bits per tick, and face the
same renewal cap. Report actual forward calls, messages, transmitted bits,
physics ticks, renewal counts, renewals by readiness, and task packets. The two
learned arms additionally have exactly the same training episodes, PPO updates,
minibatches, and parameter counts. A simpler fixed policy is not charged
synthetic optimizer work, but it receives no greater training or inference
budget than EBCR.

The strongest alternative explanation for an EBCR advantage is not useful
event detection or cooperation but a more favorable renewal frequency or
period distribution. SHUFFLE and YOKED preserve those quantities while breaking
within-episode alignment. A genuine coordination interpretation additionally
predicts a larger `COORD-LOCAL` advantage in `joint_mismatch=ON` than OFF.

## Estimands and decision statements

Base seeds are `[17,31,47,61,79,97]`. Seeds are the independent analysis units;
episodes within a seed estimate that seed's cell mean. For seed `s`, arm `a`,
and conclusion cell `c`, let

`J[s,a,c] = mean normalized episode return`.

Define:

- overall performance `P[s,a]` as the equally weighted mean of the eight cell
  means;
- robustness `W[s,a]` as the minimum of the eight cell means;
- coordination contrast `C[s] = P[s,COORD]-P[s,LOCAL]` and its analogous
  worst-cell contrast;
- timing contrast as `COORD` minus each of `COORD-SHUFFLE` and
  `COORD-YOKED`; and
- coupling interaction as `(COORD-LOCAL)_ON - (COORD-LOCAL)_OFF`, averaging
  the four tempo/noise cells inside each mismatch mode.

Report all seed-level values, means, paired effects, and ordinary two-sided 95%
Student-t intervals across the six seeds. Also report success rate, stale ticks,
renewal downtime, renewal cost, unsafe-normal-renewal cost, realized period
histograms, renewal count, boundary-to-renewal delay, simultaneous-renewal rate,
and emergency response by cell. Float calculations use ordinary numerical
tolerances; only declared integer counts, masks, and deterministic cap facts are
exact.

Counter-keyed namespaces separate phase schedules, latent initial values,
readiness chains, observation noise, actor initialization, critic initialization,
hazard uniforms, PPO minibatch order, validation selection, schedule replay, and
safety events. `LOCAL` and `COORD` share the corresponding exogenous and hazard
uniform coordinates but never parameters, trajectories, gradients, or optimizer
state.

A variable-`k` performance benefit is supported for an adaptive arm when its
paired 95% lower confidence bound over `FIXED-BEST` is above zero for `P` and
its mean `P` advantage is at least `0.02`. A variable-`k` robustness benefit is
supported when the corresponding lower bound is above zero for `W` and its mean
`W` advantage is at least `0.03`. Either statement is sufficient project value;
they are reported separately and neither may be substituted for the other.

A cooperative-renewal claim additionally requires:

1. `COORD` meets one variable-`k` benefit statement;
2. its paired lower bound over `LOCAL` is above zero on the same estimand, with
   mean advantage at least `0.01`;
3. its paired lower bounds over both timing controls are above zero, with mean
   advantage at least `0.01`; and
4. it has zero missed or pair-delayed emergency events and no cap violation.

The coupling interaction is mechanistic corroboration, not a required omnibus
gate. Report comparisons with the test-cell hindsight fixed-grid envelope and
`STAGE-ORACLE` descriptively; neither is used to select the favorable claim.

## Activity boundary and result branches

Question-relevant scientific activity begins when both learned arms have used
their first complete paired 128-tick training episodes in a valid PPO optimizer
update and emitted the associated hazard/action/count record. A process launch,
host generation, deterministic contract check, partial episode, critic-only
forward pass, or fixed-policy evaluation is preactivity engineering work.
Scientific interpretation requires both final learned checkpoints, all eight
paired conclusion cells, both schedule controls, fixed-grid selection, and the
safety panel.

Interpret complete output as follows:

- If `COORD` satisfies the cooperative criteria and its advantage is larger in
  ON than OFF, the host supports event-aligned cooperative variable-`k` renewal
  at matched caps.
- If `LOCAL` beats `FIXED-BEST` but `COORD` does not beat `LOCAL`, adaptive local
  renewal is useful here; the low-bandwidth cooperation mechanism is not.
- If `COORD` beats fixed/local but not SHUFFLE or YOKED, renewal frequency or
  period distribution remains sufficient to explain the result; do not claim
  useful event timing or coordination.
- If an adaptive arm improves `P` but not `W`, claim in-panel mean performance,
  not robustness. If it improves `W` but not `P`, claim worst-cell robustness,
  not average performance.
- If no adaptive arm beats fixed and `STAGE-ORACLE` does, the toy contains
  exploitable duration variation but the frozen hazard learner/credit/features
  did not capture it. The next discriminator is hazard-credit or observation
  sufficiency, not more seeds or a new threshold.
- If neither adaptive arms nor `STAGE-ORACLE` beat fixed, this host does not
  materially reward variable timing under the registered costs; do not enlarge
  the learner.
- If the only gain is in ON mode while OFF degrades enough to erase `P` and
  `W`, coordination is regime-specific and does not support the general EBCR
  claim. If emergency handling or a resource cap fails, make no safety or
  complete algorithm claim.

## Small registered budget

The two learned arms use
`2 arms * 6 seeds * 512 episodes * 128 ticks = 786,432` training agent-team
ticks. The fixed selection panel, eight-cell conclusion panel, timing controls,
oracle, and safety panel together are capped at 5,000,000 additional team
ticks. The whole registered train/evaluate/analyze run is capped at 6,000,000
team ticks, one CPU worker, 30 wall minutes, and 2 GiB peak RSS. It must not
silently reduce seeds, episodes, cells, controls, or horizon. A cap stop before
complete paired output is inconclusive and returns to CM as unchanged-science
engineering work.

CM should construct one isolated exogenous host, the common renewal envelope,
the two PPO arms, fixed-grid selector, replay controls, oracle, analyzer, and a
real train/evaluate/analyze entry point. Ordinary tests should cover dynamics,
masking, schedule replay, activity witness, counts, and cap accounting. The
retained result should contain declared/actual budgets, selected fixed `k`, all
seed/cell metrics and intervals, period/count distributions, control eligibility,
hazard-credit diagnostics, resource parity, emergency responses, material
anomalies, and whether the activity criterion was reached. No pre-result Pro
request is needed.

## Toy-to-UAV development path

This B1 toy isolates option-renewal timing before expensive flight dynamics.
Each object has a direct prospective mapping:

| B1 object | Second surface | UAV simulator |
|---|---|---|
| latent tracker mode | continuous target maneuver regime | target acceleration/turn regime |
| latent relay mode | fading/occlusion corridor | air-to-air/air-to-ground link regime |
| binary skill | fixed tracking/relay motion primitive | waypoint, formation, tracking, or relay option |
| skill age and innovation | residual from predicted target/link dynamics | onboard filter innovation and option age |
| readiness margin | turn-radius and connectivity margin | flight-envelope, separation, battery, and link margin |
| two-bit summary | packetized invalidation/readiness | bounded low-rate inter-UAV broadcast |
| renewal | replan or option termination | high-level skill/waypoint/role refresh |

Only a toy result that survives the count/period timing controls proceeds. The
second surface is a continuous planar two-UAV tracking--relay environment with
bounded acceleration, packet loss, occlusion, fixed low-level option policies,
and the same hidden duration/noise shifts. It preserves the same arms, safety
override, physical horizon, forward-call budget, four-bit channel, and renewal
cap while replacing binary match reward with tracking error, delivered packets,
energy, separation, and replanning latency.

Progression to the real UAV simulator requires that the same once-trained
adaptive policy still supports either performance or worst-condition robustness
over `FIXED-BEST`, and that its renewal decisions do not violate flight-envelope
or separation controls. The UAV study then varies maneuver and link-regime
durations outside training support, keeps the low-level control rate fixed, and
compares fixed `k`, local EBCR, and cooperative EBCR at matched simulated time,
physics steps, policy calls, renewal cap, and communication bits. No toy result
is transferred as UAV evidence.

## Claim ceiling

The strongest positive B1 claim is that, in this constructed two-agent,
binary-skill, exogenous-switch host, one shared learned hazard varies skill
period online and improves the named mean or worst-cell return over the frozen
fixed-`k` comparator at matched caps. If all cooperative criteria hold, the
claim may additionally attribute a local benefit to event-aligned two-bit
coordination rather than renewal-count or period-distribution differences.

B1 cannot establish UAV performance, continuous-control value, arbitrary skill
libraries, optimality of the hazard or four-bit protocol, hard safety beyond
the host override, variable-agent-count support, open-ended team coordination,
robustness outside the eight cells, or superiority to all adaptive-duration
methods. A null result is limited to this host, feature set, PPO credit rule,
budget, and costs. Missing code or infrastructure never changes that scientific
meaning.
