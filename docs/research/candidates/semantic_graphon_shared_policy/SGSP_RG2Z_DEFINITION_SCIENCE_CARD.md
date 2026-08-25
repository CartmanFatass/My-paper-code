# SGSP RIDGEGATE-2Z definition science card

```text
direction=semantic_graphon_shared_policy
portfolio_object=SGSP-TARGET-BOUND-TWO-ZONE-DEFINITION
revision=SGSP-RG2Z-SCIENCE-20260815-01
task_name=RIDGEGATE-2Z
owner=EM_semantic_graphon_shared_policy
object=definition_only_variable_N_two_zone_surveillance_relay_discriminator
scientific_activity_started=false
empirical_coordinates_bound=false
mathematical_closure=pending_same_conversation_ChatGPT_External_Pro
gemini_innovation=pending_independent_question_and_new_identity_authority
construction_authorization=none
test_or_probe_authorization=none
training_or_evaluation_authorization=none
compute_authorization=none
old_result_transfer=forbidden
```

## Conclusion first

`RIDGEGATE-2Z` is a new finite-horizon cooperative task, not a continuation or
rerun of SGSP B1. Two terrain-separated surveillance basins share a half-duplex
ridge relay service. One shared policy controls stable public roles across
training roster sizes and is deployed unchanged at smaller and larger unseen
rosters. The treatment constrains its interaction weights around a public
terrain/radio kernel fixed before the reward exists. The primary comparator is
an equally initialized, equally informed, parameter- and work-matched `EDGE`
family whose parameter domain strictly contains the treatment domain.

The single question is whether retaining that physical prior yields an
action-sensitive, task-valued cold-start advantage at one prospectively fixed
training budget after `EDGE` has demonstrated competence on the seen roster
sizes. A positive must beat `EDGE` directly at every held-out size, improve
more at held-out than seen sizes, and lose its legal-action and return advantage
when only the physical type association is broken. Anything weaker does not
retain the fixed prior for this named task.

This definition authorizes no stochastic coordinate, source, build, test,
probe, rollout, checkpoint, training, evaluation, or compute. Exact run seeds,
counter namespaces and artifact bindings remain deliberately absent under the
definition-only portfolio envelope.

## Five-line science card

- **Question.** At one fixed useful-work budget, does a terrain/radio-derived
  interaction prior protect a shared surveillance/relay policy from cold-start
  degradation at unseen fleet sizes relative to a competent strictly
  containing learned edge family?
- **Treatment.** `PHY-TRUST` uses the declared physical kernel and the same
  output-connected load-residual chart as `EDGE-FLEX`, but projects those
  residual coefficients into a narrow trust region.
- **Comparator.** `EDGE-FLEX` starts at the identical policy function, receives
  every physical and public input, uses the identical architecture and
  optimizer, and permits the same residual coefficients over a strictly wider
  box. `UNIFORM-LEGAL` is only a nonlearned competence floor.
- **Observable.** Paired seed-level task return, worst-zone timely-delivery,
  seen-versus-held-out return interaction, and a paired semantic-column cut's
  legal-action TV, return drop and treatment-versus-EDGE attenuation.
- **Strongest alternative and ceiling.** A positive may reflect useful
  constraint, normalization or optimizer preconditioning rather than semantic
  truth. It supports only a finite-budget inductive-bias claim on this exact toy
  and held-out roster set, not a learning curve, arbitrary terrain, churn, or
  UAV efficacy.

## 1. New-object and legacy firewall

The complete r06 evidence is immutable historical motivation only. No r06
roster, task state, kernel coefficient, architecture state, budget, seed,
threshold, checkpoint, tape, interval, label or result enters this object. The
only inherited qualitative lesson is the portfolio-supplied requirement that a
wrong fixed center cannot retain SGSP without a direct advantage over a fair
strictly containing `EDGE` learner.

`RIDGEGATE-2Z` has a new task, revision identity, physical law, role set,
horizon, actions, reward, treatment family, comparator family, budget,
estimands, margins and branches. It makes no statistical or pathwise contrast
to r06.

## 2. Named two-zone surveillance/relay task

### 2.1 Public roles and variable rosters

There are two static terrain basins, `WEST` and `EAST`, separated by a ridge.
Each agent has one stable public role for the whole episode:

```text
WEST-SURVEYOR
EAST-SURVEYOR
RIDGE-RELAY
```

Agents are exchangeable within role. Identity, slot, hidden rank and learned
role assignment are forbidden policy inputs. Every registered roster is
balanced with exactly `N/3` agents in each role. The one shared
parameterization trains only at

```text
N_train={9,15}
```

and is deployed without adaptation at the two held-out sizes

```text
N_heldout={6,21}.
```

Thus each public-role multiplicity is `3,5` during training and `2,7` at the
two cold-start deployments. No roster-specific head, embedding, normalization,
recurrent state initialization, calibration, finetuning or validation is
allowed. Membership and roles are fixed within an episode; the object concerns
between-sortie roster change, not churn.

### 2.2 Horizon, events, buffers and actions

Each episode has exactly 12 synchronous slots. Independently for each basin,
exactly three distinct surveillance events are assigned uniformly without
replacement to slots `0..7`. Their event IDs exist to deduplicate deliveries
and are public only inside a detected report; they are never policy identity
features. A report expires four slots after its event.

A surveyor detects a new local event with probability `0.75` only when it takes
`SCAN` in that event's slot. Its FIFO report buffer holds two reports. A relay
FIFO holds four. Overflow drops the oldest report. Relays are half duplex.

The common union action alphabet is

```text
SCAN | UPLINK | LISTEN_WEST | LISTEN_EAST | FORWARD_BASE | HOLD
```

with fixed public role masks:

- a surveyor may use `SCAN`, `UPLINK` or `HOLD`;
- a relay may use `LISTEN_WEST`, `LISTEN_EAST`, `FORWARD_BASE` or `HOLD`.

`UPLINK` attempts to send the oldest surveyor report. A relay can receive only
while listening to that surveyor's basin. `FORWARD_BASE` attempts the oldest
relay-buffer report. Packet success, collision/capture and latency are governed
by the physical law below. Both learned arms have identical masks, buffers,
messages, transition support and action probability floor.

### 2.3 Observation and shared execution

Before each decision, every agent observes its public role, slot, public role
counts, its local buffer occupancy, report ages/confidences, previous legal
action and acknowledgements. Each agent emits one fixed-width status message
per slot. A common message encoder produces `q_j`; the three role sums `Q_b`
and role counts `n_b` are the only population statistics. No learned or
physical `N x N` tensor is deployed.

The shared recurrent actor receives its local observation, receiver-role
one-hot, normalized public counts, the weighted population summary defined in
Section 4 and its physical mass. A shared role mask is then applied. Every
legal action receives at least `0.04/|A_role|` probability through a fixed
uniform mixture. Centralized training may use an identical team critic or
counterfactual baseline in both arms; neither is available at execution.

### 2.4 Reward and physical endpoints

Let `D_z` be the number of that basin's three distinct reports delivered to
base before expiry. Let `WASTE` be the fraction of non-`HOLD` radio decisions
that listen to an empty basin, uplink without a listening successful relay, or
forward an empty/failed report; define it as zero when there is no non-`HOLD`
radio decision. The episode return is

\[
J=0.65\frac{D_W+D_E}{6}
 +0.25\frac{\min(D_W,D_E)}{3}
 +0.10(1-WASTE)\in[0,1].
\]

The evaluator also records timely-delivery rate in each basin, duplicate
deliveries, expired reports, collision loss, empty listens, radio decisions
and delivered reports per radio decision. Only realized legal actions and
task return can establish value. Internal summary or weight separation is
descriptive.

The reward is defined solely from report delivery, zone balance and wasted
radio decisions. It never queries a policy kernel, edge coefficient or learned
state.

## 3. Reward-independent physical semantic kernel

The declared toy terrain has normalized public role locations

```text
WEST-SURVEYOR=(-1.0,0.0)
EAST-SURVEYOR=(+1.0,0.0)
RIDGE-RELAY=(0.0,1.5)
```

and a pre-reward nominal one-packet reception matrix, with receiver rows and
sender columns ordered `(WEST-SURVEYOR,EAST-SURVEYOR,RIDGE-RELAY)`,

\[
P^0=\begin{bmatrix}
0.92&0.48&0.88\\
0.48&0.92&0.82\\
0.86&0.78&0.90
\end{bmatrix},\qquad
L=\begin{bmatrix}
1&2&1\\
2&1&1\\
1&1&1
\end{bmatrix}.
\]

`P0` is the task's normalized ridge-shadow/link-budget model and `L` is nominal
integer packet latency. They are frozen before event generation, reward
weights, treatment parameters or data. For a sender-role multiplicity `n_b`,

\[
p_{ab}(n_b)=\operatorname{logistic}
\left(\operatorname{logit}P^0_{ab}-0.22(n_b-1)\right),
\qquad
K^0_{ab}(n_b)=\frac{p_{ab}(n_b)}{L_{ab}}.
\]

The simulator uses the underlying `P0`, latency, half-duplex and contention law
to generate packet outcomes. The policy kernel uses the separately calculated
expected timely-link coefficient `K0`; the simulator never uses a policy edge
table as an answer key. Reward relabeling or rescaling leaves `K0` unchanged.
Target-event slots and packet/action tapes are independent of arm and of every
learned edge coefficient.

This is a toy physical law, not a field calibration. Its scientific purpose is
to supply a public, independently stated interaction prior whose load law
extends to unseen multiplicities.

## 4. Treatment and strictly containing comparator

For sender multiplicities on the registered domain `n_b in {2,3,5,7}`, define

\[
v(n_b)=\frac{2\log n_b-\log 14}{\log(7/2)},
\]

so the held-out multiplicities map to `-1,+1` and the training multiplicities
lie strictly inside. Each directed role pair owns two output-connected
coefficients `(beta_ab0,beta_ab1)` and residual

\[
r_{ab}(n_b)=\beta_{ab0}+\beta_{ab1}v(n_b),\qquad
\omega_{ab}(n_b)=K^0_{ab}(n_b)e^{r_{ab}(n_b)}.
\]

There are exactly 18 trainable edge coefficients in each learned arm.

### 4.1 `PHY-TRUST` treatment

After every identical optimizer update, project each coefficient into

```text
[-0.15,+0.15].
```

The physical kernel is fixed; the learned chart permits bounded calibration
without discarding its role/load structure.

### 4.2 `EDGE-FLEX` comparator

Use the same chart and projection operation but the strictly wider coefficient
domain

```text
[-1.50,+1.50].
```

Every `PHY-TRUST` parameterization is therefore literally an `EDGE-FLEX`
parameterization with identical action probabilities on every legal input and
registered roster. A coefficient value `0.60` with an output-connected actor
is an explicit strict-capacity witness unavailable to `PHY-TRUST`.

Both arms initialize every edge coefficient at zero, copy every common tensor,
and therefore begin at the identical complete policy function `omega=K0`.
They use the identical coordinate chart, derivatives and optimizer state
throughout the shared interior. Every edge coefficient is output-connected;
there is no frozen padding, delayed gate, dummy operation or unused parameter.

### 4.3 Shared implicit aggregation

For receiver role `a`,

\[
D_a^A=\sum_b n_b\omega^A_{ab}(n_b),\qquad
Z_a^A=\frac{\sum_b\omega^A_{ab}(n_b)Q_b}
{D_a^A+10^{-12}}.
\]

The actor receives `(Z_a,D_a,public counts,receiver role,local observation)`.
Both arms use three role reductions, nine physical-kernel evaluations, 18
residual multiply-adds, nine exponentials and one actor call per agent. Both
send one equal-width status message per agent per slot. Parameter count,
communication, useful forward/backward operations, rollout count, optimizer
opportunity and recurrent state are identical. Deployment is implicit
`O(N+9)` work and `O(N)` message storage.

## 5. One prospective budget and competence gate

The sole prospective training budget is

```text
512 optimizer updates
64 complete 12-slot episodes per update
32 episodes at each N_train per update
only_evaluable_checkpoint=immediately_after_update_512
```

Both arms receive identical episode, event, packet, action and initialization
tapes within a future seed block, the same update/batch order, identical
optimizer hyperparameters, gradient calls and clipping, and no validation
selection or early stopping. Held-out rosters may not be materialized for
training, normalization, adaptation, replay, calibration or checkpoint choice.
No earlier/later checkpoint or second budget belongs to this object.

`UNIFORM-LEGAL` samples uniformly from each role's legal mask and is evaluated
on the same worlds solely as a task/competence floor. It is not a matched
algorithmic comparator and cannot retain the physical prior.

`EDGE_TRAIN_COMPETENT` requires, at both training sizes:

1. the simultaneous lower bound for `EDGE-FLEX - UNIFORM-LEGAL` return exceeds
   `0.08`; and
2. the two-sided `PHY-TRUST - EDGE-FLEX` interval lies wholly inside
   `[-0.04,+0.04]`.

Thus a retained cold-start claim cannot arise because `EDGE-FLEX` simply failed
to learn the seen-size task or was already materially inferior before the
roster shift.

## 6. Prospective inference and coordinate boundary

A later empirical object, if separately authorized, uses 24 independent
training-seed blocks and 256 fresh evaluation episodes per registered roster
and seed. Seeds, not agents, slots, packets, events or episodes, are the
inferential units. Arms are paired within an exact seed/roster world. Different
roster sizes occupy independent world coordinates conditional on the same
trained checkpoint and are never treated as pathwise pairs.

The exact 24 seed labels, counter namespace, run root, certificate and artifact
coordinates are intentionally unbound because this portfolio layer forbids
coordinate binding. Their later prospective binding cannot reuse any old SGSP
identity or observed value and must preserve the count, independence, pairing
and inferential law here. If that binding changes a science-bearing condition,
the resulting complete composite requires another same-conversation Pro
ruling before activity.

Use paired seed-level Student-`t` intervals under one prospectively fixed
Bonferroni family. It contains exactly 18 quantities: four direct roster
contrasts; two training-size `EDGE-FLEX - UNIFORM-LEGAL` competence contrasts;
two cold-start interactions; two held-out worst-zone contrasts; the three
semantic-cut quantities at both held-out sizes; and two held-out return-
answerability quantities. Construct every quantity with two-sided per-contrast
error `0.05/18`, so the complete family-wise error is at most `0.05`. Branches
use the registered lower/upper endpoints of those intervals; no allocation is
chosen from observed results.

For seed `s`, let

\[
d_s(N)=J^{PHY}_s(N)-J^{EDGE}_s(N),
\]

\[
d_s^{seen}=\tfrac12[d_s(9)+d_s(15)],\qquad
c_s(N)=d_s(N)-d_s^{seen},\quad N\in\{6,21\}.
\]

Fresh task-unit margins are

```text
direct return margin delta_R=0.04
cold-start interaction margin delta_C=0.03
worst-zone delivery margin delta_Z=0.02
cut return-drop margin delta_cut_R=0.05
cut legal-action-TV margin delta_TV=0.08
advantage-attenuation margin delta_I=0.03
```

No value or rationale comes from r06. Four return points correspond to a
substantive change on the normalized delivery/balance/waste score; the smaller
interaction and zone margins require the effect to be specifically roster-
linked and not purchased by sacrificing one basin.

For each held-out size, return is answerable only when the simultaneous lower
bound for the within-seed minimum of

```text
J_PHY, J_EDGE, 1-J_PHY, 1-J_EDGE
```

exceeds `delta_R`. A false answerability flag is floor/ceiling saturation, not
equivalence, inferiority or mechanism failure. Complete atomic evidence also
requires both basins/events/role paths to have positive support, exact legal
action support, fixed masks, no leakage, matching, nesting and finite outputs.

## 7. Action-sensitive physical-kernel intervention

At each held-out size, `SEMANTIC-COLUMN-ROTATE` is a paired treatment-only
evaluation intervention. For every receiver row, rotate the physical sender
columns

```text
WEST-SURVEYOR -> EAST-SURVEYOR -> RIDGE-RELAY -> WEST-SURVEYOR
```

while leaving learned residual coefficient indices, public counts, sender
messages, receiver role, local observations, recurrent/actor parameters,
physical simulator, target events, reward, legal actions and exogenous tapes
unchanged. Balanced roles preserve every receiver-row coefficient multiset.
The intervention breaks only which public sender type receives which physical
coefficient.

On intact predecision histories, shadow replay gives mean legal-action TV
between intact and rotated treatment policies. Full paired counterfactual
rollouts give

\[
C_s(N)=J^{PHY,intact}_s(N)-J^{PHY,rotate}_s(N),
\]

and fixed-versus-EDGE attenuation

\[
I_s(N)=d_s^{intact}(N)-
[J^{PHY,rotate}_s(N)-J^{EDGE,intact}_s(N)].
\]

`KERNEL_USE_PASSES` requires simultaneous lower bounds above `delta_cut_R`,
`delta_TV` and `delta_I` at both held-out sizes. A summary change is
insufficient. Cut harm cannot rescue a failed intact comparison.

## 8. Result-blind outcome branches

Apply the separate result-blind map literally and in order.

1. Structural invalidity, incomplete evidence, leakage, matching failure or
   noncontainment returns no scientific relation.
2. Failed return answerability, failed legal-action support or failed
   `EDGE_TRAIN_COMPETENT` returns `NONIDENTIFIED`; it cannot delete or retain
   either family.
3. `RETAIN_PHYSICAL_PRIOR_COLDSTART` requires all validity/answerability and
   competence gates; direct held-out lower bounds above `delta_R` at both
   sizes; cold-start interaction lower bounds above `delta_C` at both sizes;
   worst-zone delivery lower bounds above `delta_Z` at both sizes; and complete
   `KERNEL_USE_PASSES`.
4. Every other complete, valid, answerable panel with competent `EDGE-FLEX`
   selects `DO_NOT_RETAIN_FIXED_PRIOR_AS_DEFAULT`. Subreason labels distinguish
   practical equivalence, EDGE superiority, mixed/nonrobust roster effects and
   absent action-sensitive attribution, but none authorizes another budget or
   wrong-center rescue.

This is a decision about the fixed physical-prior restriction relative to the
containing learner for this exact named task and budget. It is not universal
algorithm deletion.

## 9. Strongest alternative

Even a fully qualifying positive cannot distinguish correct semantic knowledge
from the entire package of a narrower projection domain, load normalization,
curvature, regularization and optimizer preconditioning around a physically
reasonable table. Identical initialization, shared local chart, exact nesting,
training-size competence, cold-start interaction and semantic-cut attenuation
make a pure comparator-handicap explanation less plausible but do not identify
kernel truth or faster learning.

The strongest rival is that `PHY-TRUST` is simply a better finite-budget
regularizer for this simulator while `EDGE-FLEX` needs more useful work. That
is still a bounded package-level inductive-bias result at the fixed budget, not
an asymptotic or ontological semantic claim.

## 10. Claim ceiling and UAV boundary

A fully qualifying positive supports at most:

> In the exact static two-basin `RIDGEGATE-2Z` toy, one shared policy whose
> role/load interactions remained near a reward-independent terrain/radio
> kernel achieved an action-sensitive return advantage over a competent,
> equally initialized and strictly containing matched edge learner at the two
> adaptation-free held-out roster sizes after exactly 512 matched updates; the
> advantage was larger than at the seen rosters and was not purchased by
> sacrificing one basin.

It does not establish a learning curve, faster convergence, asymptotic
superiority, kernel truth, unique physical correctness, benefit at another
budget or roster, arbitrary terrain or role mixtures, dynamic membership,
churn, mobile zones, nonstationary fading, hidden roles, perception validity,
continuous flight dynamics, collision safety, energy feasibility, regulatory
compliance, real-radio performance, a second surface, or UAV mission benefit.

The toy-to-UAV mapping is limited but concrete: west/east surveyors generate
time-limited observations, ridge relays allocate half-duplex reception and
forwarding, and changing fleet size changes contention while public role
physics remains stable. A positive would justify only later portfolio
consideration of this physical-prior component; it would not authorize UAV
simulation or production.

## 11. Definition-only activity and authority boundary

Scientific activity begins with the earliest materialization, generation,
inspection, summary or use of a new-task initialization, episode event,
detection, packet, action, evaluation world, policy output, checkpoint or
endpoint. Static symbolic reasoning and CM read-only feasibility/cost analysis
remain preactivity.

Before any empirical construction, the definition must receive exact
same-conversation ChatGPT External Pro `CLOSED` and EM intake. The independently
blind Gemini question may supply hypotheses but cannot close the object. CM may
then perform only the portfolio-authorized static bindability, observability,
comparator-feasibility and prospective-cost review. Pro closure and CM static
feasibility authorize no source, build, test, probe, coordinate, rollout,
training, evaluation, compute lease, second surface or UAV action. Any such
next stage requires a new portfolio decision and Root envelope.
