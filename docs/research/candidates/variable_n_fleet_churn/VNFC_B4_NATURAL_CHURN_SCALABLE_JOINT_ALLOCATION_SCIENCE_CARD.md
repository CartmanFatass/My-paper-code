# VNFC-B4 natural-churn scalable joint-allocation science card

Owner: `direction:variable_n_fleet_churn_b4` Explorer Manager  
Treatment: `VNFC-B4-NATURAL-CHURN-SCALABLE-JOINT-ALLOCATION`  
Revision: `VNFC-B4-SCIENCE-20260815-05`  
Current authority: definition, External-Pro mathematical/causal closure,
independent innovation consultation, and CM static feasibility only

## Decision and non-transfer boundary

This is a new treatment identity. It is not VNFC-B3 v8 repair, v9, a second
surface, or a UAV experiment. It inherits no VNFC-B1/B3 seed, threshold, panel,
host row, checkpoint, result, feasibility observation, acceptance, closure, or
claim. Prior VNFC work supplies only the recorded same-direction ChatGPT Pro
conversation identity and the design warning that a physical history must arise
before, and independently of, treatment outcomes.

This revision defines a complete prospective scientific object but authorizes no
construction, test, probe, seed or coordinate binding, compute, lease, or
question-relevant activity. The numerical values below are new B4 definitions,
not inherited experimental coordinates. Machine PRNG integer labels remain
unbound in this definition-only stage; the sixteen independent replicate roles,
their namespace separation, all distributions, counts, estimands, margins, and
analysis are fixed. A later empirical authorization may assign fresh injective
machine labels to those exchangeable roles before construction without changing
this scientific object. No outcome may inform that assignment.

## Question

On a fixed two-task physical-time service surface with one exogenous join or drop,
can a single shared permutation-equivariant bidder trained only with active roster
sizes at most five produce agent-associated learned bids whose common scalable
Residual-Demand Allocation rule (`L-RDA`) has greater held-out task value or
post-event robustness at active roster size seven than:

1. the registered full-horizon, physics/history-aware independently indexed
   nonlearned bids through the same allocator (`FIXED-RDA`);
2. a same-information, same-interaction-budget, containing learned joint-set
   policy (`DIRECT-SET`); and
3. the same L-RDA checkpoint after whole bid rows are reassociated among
   feasibility-equivalent agents (`L-RDA-PERMUTE`)?

`BEST-RDA` and `GLOBAL-EXACT` are offline ceilings. They distinguish absent
learnable headroom from an inadequate RDA action grammar. The environmental
action is the final joint destination set, not the real-valued bid vector.

## Physical-time host

### Fixed service graph and clock

The host has base `B` and two persistent service sectors `S1,S2`. There are no
continuous coordinates. Physical travel times are fixed graph facts:

| Edge | standard vehicle | fast vehicle |
|---|---:|---:|
| `B <-> S1` | 40 s | 20 s |
| `B <-> S2` | 40 s | 20 s |
| `S1 <-> S2` | 60 s | 40 s |

Time is simulated in one-second increments. Allocation decisions occur every
twenty physical seconds. An agent already on an edge must finish that edge before
receiving a new destination; the feasibility mask exposes this commitment. On
arrival at a sector, five consecutive seconds of acquisition dwell are required
before coverage begins. An agent covers only its assigned sector and contributes
at most one unit of coverage. Under the deployable RDA grammar, at most one agent
may be targeted to each sector; every other free agent is targeted to `B`.

Acquisition persists only while an agent remains assigned to the same sector.
Changing destination immediately clears acquired status and dwell; a later sector
arrival starts a fresh five-second acquisition. Reissuing the same sector to an
already acquired stationary agent preserves acquisition. Arrival at base clears
acquisition and dwell.

Flight consumes one energy unit per second, acquired sector service consumes
`0.2` energy unit per second, and base charging restores two units per second up
to capacity. A real-sector destination at boundary `t` is legal only when the
following exact contingency rollout never takes energy below twenty units: obey
any existing edge commitment; travel to the candidate; acquire it; keep that
candidate through the first decision boundary at or after acquisition completion
that is not earlier than `t+20`; and then choose `B` at every subsequent decision,
finishing each edge commitment, until base is reached. The candidate action is
held at least through `[t,t+20)`, and the contingency includes any travel,
acquisition, or service that necessarily extends beyond that interval. This same
mask test is recomputed at every decision. If a sector fails it, that sector is
illegal; when both sectors fail, only `B` is legal. There is no between-decision
auto-return, reserve borrowing, or mid-edge redirection. Thus the mask covers the
complete action-hold and safe-return obligation rather than only route acquisition.

Each agent has one of the four observable crossed types

`{standard,fast} x {100,140 energy-unit capacity}`.

Type, initial energy, and every later physical state are inputs, never opaque
identity embeddings. Each world has exactly seven latent identities. Draw one
uniform permutation of the four crossed types for identities 1--4 and an
independent uniform permutation of the four types whose first three entries type
identities 5--7. Draw a separate uniform roster ordering of the seven identities.
An initial active roster of size `N` is the first `N` identities in that ordering;
a join activates the next two, and a drop deactivates the last two members of the
active prefix. Consequently the post-event roster is again a prefix. The marginal
type of a uniformly selected active row is uniform over the four crossed types at
every roster size. The joint count law is exactly the prefix-sampling law just
stated and is not described as literally balanced at `N=3,5,7`. No composition or
world is accepted, rejected, or redrawn in response to an outcome.

### Task demand and value

Each sector has public demand state `q_r(t) in {1,2}`. At `t=-120`, draw each
state independently from its stationary distribution, uniform on `{1,2}`. At
every later twenty-second boundary, including `t=0`, it stays unchanged with
probability `3/4` and flips with probability `1/4`, independently by sector and
boundary. The complete demand tape is sampled before any treatment branch,
remains hidden beyond the current state, and is coupled across arms by physical
time.

Let `c_r^a(t)` equal one when arm `a` has an acquired, energy-feasible covering
agent at sector `r` at physical second `t`, and zero otherwise. For the 120-second
post-event horizon define

`Y_a = integral_0^120 sum_r q_r(t)c_r^a(t)dt /
       integral_0^120 sum_r q_r(t)dt`

and the one-event robustness functional

`R_a = integral_0^40 sum_r q_r(t)c_r^a(t)dt /
       integral_0^40 sum_r q_r(t)dt`.

Both lie in `[0,1]`, use physical seconds rather than decision count, and are
higher-is-better. The team training return is `U_a=(Y_a+R_a)/2`. There is no
explicit switch/keep reward, role-retention bonus, per-agent reward, or
decision-count discount. Continuing, redirecting, replacing, charging, and
handoff loss arise only from travel, acquisition, energy, and coverage physics.

### Treatment-blind natural prehistory

At `t=-120`, all seven latent identities are at `B`, have their type-specific full
energy, destination `B`, no residual edge or acquisition dwell, and three prior
destinations padded with `B`. Active age and inactive age are both zero. The
initial roster prefix for that schedule is active; every other identity is an
inactive reserve at base and follows the same charging and history clock while
inactive. Demand has the independently drawn initial state defined above, and
each sector's three lagged demand entries is padded with that same initial state.
At each later boundary, destination and demand histories shift once before the
new current entries are exposed.

Independently of type, roster order, demand, and every arm, draw one uniform
permutation of the seven identities as the world's opaque identity tie rank. It
is fixed across prehistory, learned arms, fixed arms, and ceilings. Assignment
ties then use sector order `S1,S2,B` followed by this rank. Also draw, for each
world and every decision boundary, one fresh uniform permutation of the currently
active input rows. The permutation is common to all executable arms and
checkpoints at the same world and physical time, independent of outcomes, and is
mapped back through simulator handles after action selection. Handles and ranks
are never actor, critic, or fixed-bid features.

For every world, simulate `[-120,0)` for six twenty-second decisions under one
deterministic `PREHISTORY-FIXED-RDA` controller. At each prehistory decision
boundary `t in {-120,-100,-80,-60,-40,-20}`, set `H=t+40`. For a currently active
free agent `i` and legal first destination `x`, define

`C_i[t,H) = integral_t^H sum_r q_r(s)c_i,r(s)ds`,

`D[t,H) = integral_t^H sum_r q_r(s)ds`,

and

`Q_i^pre(o_t,x) = sup_pi E[C_i[t,H)/D[t,H) | o_t,a_i(t)=x]`.

The supremum is over nonanticipating single-agent destination choices at the
single later decision boundary `t+20`. There is no action at `H` and no
contribution at or after `H`. Demand follows the registered Markov law. When
`H>0`, the calculation still assumes the current roster persists through `H`
and applies no membership event. Other agents supply no hypothetical coverage
inside this single-agent calculation. Since both sector demands are always in
`{1,2}`, the denominator is strictly positive.

Set `b_i^pre(x)=Q_i^pre(o_t,x)-Q_i^pre(o_t,B)` and `b_i^pre(B)=0`, then apply the
common RDA action and tie law. All currently active and reserve agents, current
destinations, residual edges, acquisition dwell, energy, coverage, task demand,
and the last sixty seconds of physical records evolve normally under the chosen
joint allocation.

The prehistory controller observes neither the event kind nor the affected
identities before `t=0`; its forty-second model assumes roster persistence even
when that lookahead crosses time zero. Presampling the event is only a coupling
device for the world generator and does not expose it to prehistory.

The membership event, affected immutable identities, agent types, task-demand
tape, row permutations, tie rank, and all future exogenous innovations are
sampled before prehistory and are independent of treatment and reward. Every
decision boundary `t in {-120,-100,...,100}` has this single ordering:

1. the preceding half-open physical interval has completed (there is no preceding
   interval at `t=-120`);
2. at `t=0` only, apply the sole membership event: joining prefix identities become
   active at `B` with their accumulated inactive energy and history; dropped
   identities become inactive immediately without erasing prior service. For the
   full `[0,120)` horizon, joined identities carry `(newly_joined,survivor)=(1,0)`
   and every identity active before the event that remains carries `(0,1)`; the
   global event-kind one-hot likewise remains fixed;
3. at `t=-120`, expose the initial demand draw; at every later boundary, including
   `t=0`, apply the presampled demand transition before any action;
4. recompute route/energy masks and the observable state, and apply the common
   fresh active-row permutation for that world and time;
5. choose the joint allocation; and
6. simulate `[t,t+20)` one physical second at a time.

Within each physical second, first advance travel by one second or, for an agent
already at base, charge by two units. Travel subtracts one energy unit; stationary
acquisition itself consumes no energy. An unacquired agent at its destination then
spends that entire second on acquisition and decrements its dwell counter by one,
but supplies no coverage during that second. An agent that was already acquired
at the start of this acquisition/service phase consumes `0.2` energy and supplies
coverage for that second. Demand is constant throughout the interval. Arrival may
start the first of five acquisition seconds in the same tick, but coverage starts
only on the following tick after all five have completed. Legal-mask contingency
simulation uses this identical phase order. At tick end, an active identity's
active age or an inactive identity's inactive age increments by one and saturates
at `120`; the nonapplicable age is zero. A join resets active age to zero and a
drop resets inactive age to zero. Destination histories shift only at decision
boundaries, including a repeated destination when an edge commitment persists.

At `t=0`, after the event and demand transition but before any arm action, clone
the complete observable and hidden simulator state into every arm; the already
sampled row permutation is applied identically to each clone. Both public
cumulative-demand fields are reset to zero at `t=0`; during each post-event
physical second, add the current two-sector demand sum to `D_Y^past` and, only
while `t<40`, to `D_R^past`, exposing the updated totals at the next boundary.

No inclusion, top-up, retry, history class, or world retention rule observes an
arm, bid, action, return, ceiling, or future treatment outcome. There is no
artificial `KEEP/SWITCH` bank and no certificate-selected prehistory.

## Variable-N distribution

Training uses exactly equal numbers of one-event schedules `3->5` and `5->3` in
every update. No learned
actor or critic is trained, validated, tuned, stopped, or checkpoint-selected on
an active roster larger than five.

Conclusion uses equiprobable schedules `5->7` and `7->5`. The `5->7` join cell is
the sole held-out above-training active-roster claim cell. The drop cell supplies
the matched loss/recovery stress but does not by itself establish above-training
execution after the event. Initial and post-event identities are exactly the
roster prefixes defined above; there is no additional join/drop sampling,
composition constraint, top-up, or support-conditioned redraw.

Every learned arm uses one unchanged parameterization, observation normalization,
checkpoint, action rule, and threshold across `N=3,5,7`. No per-`N` head, roster
slot embedding, calibration, fine-tuning, or evaluation adaptation is allowed.

## Information available at execution

For each active agent the unordered row contains:

- observable vehicle type and energy capacity;
- current node or exact residual directed edge and remaining travel seconds;
- energy, assigned destination, acquired/not-acquired state, and remaining dwell;
- active/inactive age, newly joined/survivor bit, and the prior three decision
  destinations; and
- exact travel time and energy reserve feasibility to `B,S1,S2`.

The two persistent sector rows contain sector identity, current demand, current
covering/committed-agent indicators, and the preceding three demand states.
Global public fields are physical time remaining, event kind, and
`log(1+N)`, plus the action-independent cumulative demand denominators observed
so far: `D_Y^past(t)=integral_0^t sum_r q_r(s)ds` and
`D_R^past(t)=integral_0^min(t,40) sum_r q_r(s)ds`. These are demand history, not
arm reward or coverage. Opaque simulator handles are used only to map rows back
after a fresh input permutation; they are not neural or fixed-bid inputs.

Literal encodings are fixed. Vehicle speed and energy-capacity class are separate
two-way one-hots. Physical location is a nine-way one-hot over `B,S1,S2` and the
six directed graph edges; destination is a three-way one-hot. Each of the three
prior destinations is a three-way one-hot. Acquired, newly joined, survivor,
active, and every route/energy feasibility flag are binary. Residual travel,
remaining dwell, physical time remaining, and active/inactive ages (the
nonapplicable age is zero) are divided by `120`, except dwell is divided by `5`.
Energy and capacity are divided by `140`; exact travel-time features are divided
by `120`; demand and its three lags are divided by `2`; and the roster scalar is
`log(1+N)/log(6)` with no clipping, so held-out `N=7` is deliberately above the
training normalization range. `D_Y^past` is divided by `480` and `D_R^past` by
`160`, their respective maximum denominators. No empirical or learned feature
normalization is permitted.

`L-RDA`, `DIRECT-SET`, and `FIXED-RDA` receive exactly this information, subject
to their declared functional form. No executable arm observes future demand,
future membership, realized return, advantage, critic output, ceiling action or
value, another arm, seed label, or treatment identity. Each training-only
state-value critic receives only the same unordered post-event state at `t=0`,
never an action or a future exogenous fact.

## Common scalable allocator and RDA reachability

At a decision, let `F_R(o)` be the finite set of joint destination assignments in
which every free active agent selects one of `B,S1,S2`, each sector receives at
most one newly targeted or already committed agent, all route/energy masks pass,
and en-route agents retain their commitment. Base has unlimited capacity.

`RDA(b,o)` returns the member `X in F_R(o)` maximizing the sum of its selected
free-agent destination bids; committed-agent terms are fixed constants and are
omitted. Equal scores are resolved by the lexicographically first complete
assignment: compare the identity assigned to `S1`, then `S2`, then the base list,
using the world-fixed opaque identity rank and an empty-sector sentinel after all
identities. For fixed two-sector tasks,
the legal real-sector candidates can be enumerated in `O(N^2)` time and `O(N)`
live memory; no `N x N` learned tensor, roster-indexed output bank, reward call,
rescore after allocation, exact physical-value fallback, or arm-specific rule is
permitted.

Conditional on supplied bids, the allocator receives only the active/free mask,
route/energy feasibility mask, already committed destinations, and fixed tie
rank. It receives no demand, task value, physical history, reward, return,
critic, learned parameters, arm label, future fact, or ceiling. It is therefore
reward-input-blind conditional on bids. The L-RDA bidder is reward-trained and
must never be described as reward-blind.

For any `X in F_R(o)`, assigning bid `+2` to every edge selected by `X` and `-2`
to every other legal edge makes `X` the unique allocator maximizer. Thus RDA is
surjective onto `F_R(o)`. This witness defines `BEST-RDA` reachability; it does
not say that a learned or fixed bidder can find the witness.

## Executable arms

### L-RDA

A shared permutation-equivariant set bidder uses:

- agent encoder: two fully connected SiLU layers of width 64;
- sector encoder: two fully connected SiLU layers of width 32;
- context: agent embedding sum and mean, both sector embeddings, global fields,
  and the candidate agent/sector embeddings;
- edge head: fully connected widths `96,64,32,1`; and
- base head: fully connected widths `64,32,1` shared across agents.

The edge-head input is the concatenation of the candidate agent embedding,
candidate sector embedding, agent-embedding sum and mean, both ordered persistent
sector embeddings, and global fields. The base-head input is the same
concatenation with no candidate-sector term. “Shared” means one set of head
parameters is reused for every applicable row, edge, roster size, and decision.
Every hidden layer in the edge and base heads uses SiLU; each final scalar bid
output is linear. The agent and sector encoders likewise use SiLU after each of
their two hidden linear layers and have no additional output nonlinearity.
All feature names above are fixed; CM derives only their literal tensor width.
No agent-agent attention or roster-slot parameter is allowed. The actor emits one
real bid per legal agent-sector edge and one base bid per free agent. During
training, every legal emitted bid is an independent
`Normal(mu_e,0.30^2)` latent variable before the common allocator. Evaluation
uses the deterministic means. Illegal masked variables are neither sampled nor
included in a likelihood.

For decision `d`, the latent-policy log density is the sum of the Gaussian log
densities for every legal free-agent bid variable at that decision. The
six-decision trajectory log density is the unnormalized sum of those six
decision-level sums. No division by legal-edge count, agent count, or decision
count occurs inside the PPO likelihood ratio. The single trajectory advantage is
applied once to that trajectory log density; agent or edge terms are not treated
as independent returns. An empty latent-variable sum is zero.

### DIRECT-SET containing learned comparator

`DIRECT-SET` receives the identical unordered information and uses the identical
agent/sector encoders and aggregation widths. At every decision it has two
explicit candidate branches:

1. **embedded branch:** the exact L-RDA bidder, independent
   `Normal(mu_e,0.30^2)` legal-bid distribution, common RDA mapping, and tie law;
2. **residual branch:** enumerate `F_R(o)` and give assignment `X` score
   `sum_(e in X) mu_e + rho(X)`, where `rho` is a permutation-invariant residual
   from the sum and elementwise max of selected free-agent/destination embeddings
   through widths `64,32,1`. A selected base destination concatenates the agent
   embedding with one shared learned base token; sector destinations use their
   sector embedding. If there is no free agent, sum and max are both the all-zero
   vector. The same residual parameters are shared across every assignment and
   roster size. Training samples from the temperature-one categorical
   softmax of these complete-assignment scores; evaluation takes their maximum
   under the common tie law.

A pooled-context gate whose input is agent-embedding sum and mean, both ordered
sector embeddings, and global fields and whose widths are `64,16,1` emits `z` and
`p_emb=clip((z+1)/2,0,1)`. Training samples a Bernoulli branch. Evaluation chooses
the embedded branch when `p_emb>=0.5` and the residual branch otherwise. The
residual head and pooled-context gate use SiLU after every hidden linear layer;
their final scalar outputs `rho(X)` and `z` are linear before, respectively, score
addition and the stated hard-sigmoid clipping. The
parameter space therefore contains L-RDA exactly: copy every L-RDA bidder
parameter and set the gate to `p_emb=1` for every state. This reproduces L-RDA's
Gaussian latent-bid distribution, allocator mapping, and tie law at every roster
size, including `N=7`; no claim is made that a categorical softmax alone matches
Gaussian-perturbed argmax probabilities.

At each training decision the DIRECT likelihood is the Bernoulli gate log
probability plus the selected branch's joint log probability: the sum of Gaussian
bid log densities for an embedded draw, or the one categorical assignment log
probability for a residual draw. Its trajectory log probability is the sum over
all six decisions. The residual and gate heads give the containing control
additional active parameters, which must be reported. This asymmetry is
deliberate: a positive L-RDA result can support only finite-budget inductive
bias/trainability relative to a more expressive containing control, never
superior expressivity.

DIRECT-SET is matched to L-RDA in raw observation, actor/critic backbone,
training worlds, reward evaluations, update count, optimizer, checkpoint rule,
row permutations, model-selection opportunity, and one executed environment
action per decision. It does not receive an extra outcome query for each enumerated
candidate. Its two-sector enumeration is `O(N^2)` time and `O(N)` live memory.
For that bound, precompute the all-base residual sum and the top three base-row
values in every fixed embedding coordinate. Any `F_R` assignment replaces at
most two base rows, so its sum and elementwise max are updated in constant time
per fixed coordinate; rescanning all `N` rows per assignment is forbidden.

The categorical residual assignment log probability is one joint-set term, not
a sum of independently credited agent decisions.

### FIXED-RDA

For every free agent `i` and legal first destination `x`, solve an exact
single-agent finite-horizon dynamic program from the current decision through
`t=120`. Its first action is fixed to `x`; at later twenty-second boundaries the
single agent may choose any reserve-feasible destination nonanticipatingly from
its then-current observable state. The program integrates exactly over the
declared Markov demand law, including both sectors because the realized
normalizing denominators of `Y` and `R` depend on both. It maximizes the expected
remaining contribution to `U=(Y+R)/2`, conditional on observed demand history,
current physical state, and already realized demand before the decision. It never
receives the realized future tape. Other agents supply no hypothetical future
coverage inside this single-agent index; actual current en-route commitments
remain represented by the common action mask.

The public cumulative demand fields make the normalized-ratio expectation exact.
Past arm coverage is not an input: it is the same additive numerator term for
every candidate first action and cancels in `Q_i(o,x)-Q_i(o,B)`.

Let that exact action value be `Q_i(o,x)`. Set the sector bid to
`Q_i(o,x)-Q_i(o,B)` and the base bid to zero, then pass all bids through the
identical RDA allocator. The future single-agent policy is a calculation used to
define a bid, not an extra environment action or outcome query. This calculation
uses current demand and its history, route, energy, dwell, age, prior destination,
and the complete declared physical law; it has no fitted coefficient, learned
parameter, treatment outcome lookup, future realized tape, or treatment label.
Exact transition-model knowledge is a favorable structural prior supplied to
this comparator and must be disclosed in every result interpretation.

`PREHISTORY-FIXED-RDA` uses the exact normalized forty-second construction in the
prehistory section, including its half-open horizon, sole later decision, and
no-event model. It still observes no fact about the presampled event. Post-event
FIXED-RDA's full-remaining-horizon alignment removes the trivial alternative that
a learned arm wins only because the analytic comparator cannot value travel whose
payoff occurs after forty seconds.

This is the strongest registered physical/history-aware independently indexed
nonlearned comparator: its fixed interface is a sum of separately calculated
agent bids through the common allocator. `BEST-RDA` below is the stronger exact joint
current-information policy ceiling, so any FIXED comparison is interpreted only
with that ceiling. An L-RDA comparison with a weaker ETA-only, capability-only,
zero, random, or history-free rule has no claim-bearing role.

### L-RDA-PERMUTE

Freeze the final L-RDA checkpoint. At each evaluation decision, after all learned
bid rows are emitted and before RDA sees them, uniformly derange complete
free-agent bid rows within each block having the same crossed vehicle type and
identical three-destination route/energy feasibility mask. En-route agents, whose
sole legal commitment is not an allocation contest, remain unchanged. This
prevents a cross-speed or cross-capacity swap from constituting the intervention;
within a block, physical location, exact energy, age, and history remain the
agent-associated information being cut. Preserve task columns, base bid,
within-row correlation, row multiset, task state, allocator, tie rank, membership,
and exogenous tape. Do not retrain.

The permutation distribution is exact. For conclusion world `w`, variant
`k in {0,...,7}`, and decision time `t`, form the registered free-agent blocks
from that variant's reached state. Within each block, order members by ascending
opaque identity rank. For a block `G` of size `m>=2`, draw one permutation
uniformly from all fixed-point-free permutations of positions `{0,...,m-1}`. A
block of size zero or one uses the identity map. If `sigma` is the drawn map, the
complete bid row emitted for source position `sigma(j)` is assigned to the
physical agent at block position `j`.

Conditional on the reached state, block derangements are mutually independent
across distinct blocks. They are also independently keyed across physical times,
variants, worlds, and replicate roles. The exact counter key is
`(replicate role,"conclusion-permute",world coordinate,variant k,physical time,
ordered tuple of member opaque ranks)`. No stateful draw ordering or shared
random rank may couple distinct blocks.

At each of the six decisions in each of eight full-rollout variants, apply that
exact law to the permuted rollout's own current state. Average the eight complete
120-second outcomes before the world enters inference. A block with fewer than
two members is unchanged and contributes no association opportunity. This
intervention cuts the bid-to-originating-agent relationship without changing
immediate feasibility support. Its validity requires the prospective
association-opportunity and action-sensitivity conditions below.

## Offline ceilings

Both ceilings are exact nonanticipating feedback policies under the known host
and demand-transition law. At each reached decision state they receive exactly
the public observation listed for executable arms, including cumulative demand
but not cumulative arm coverage or return, and may condition a future action only
on observations available when that future boundary is reached. They never
receive the realized future demand tape. Computation may be performed offline,
but the evaluated policy is current-information causal and contains no
clairvoyance.

`BEST-RDA` is the single Bayes-optimal feedback policy for expected
`U=(Y+R)/2` when every action lies in `F_R(o)`. Every chosen action is passed
through the common allocator using its `+2/-2` witness bids. `GLOBAL-EXACT` is
the single expected-`U`-optimal feedback policy over `F_G(o)`, the larger safe grammar
in which every free agent receives a destination and, for each sector, the action
also designates at most one acquired or on-arrival agent as active server.
Multiple agents may occupy or target a sector; non-designated acquired agents are
standby, consume no service energy, and supply no coverage. The designated agent
alone consumes service energy and supplies at most one unit of sector coverage.
Designation can change only at decision boundaries. Travel, acquisition, reserve
tests, commitment, charging, and the tick order are otherwise identical to RDA.
Each GLOBAL reserve contingency uses that action's designation through the
current hold: it charges service energy only for the designated server and then
uses the same first-feasible-boundary return-to-base continuation for every
targeted agent.

The solver state includes the public elapsed-demand accumulators, so expected
normalized `Y`, `R`, and hence `U` are optimized literally rather than by a
ratio-of-expectations surrogate. Past arm coverage is action-independent at a
decision and cancels from comparisons; it may be carried by the evaluator for
final scoring but is neither a policy input nor a Bellman branching variable.
Equal expected `U` is broken by greater expected `Y`, then greater expected `R`,
then the following unique canonical action serialization. Give opaque identity
ranks the integers `1,...,7` and use sentinel `8`. Serialize a GLOBAL action as
`[server(S1),members(S1),server(S2),members(S2),members(B)]`, where each server
entry is its designated-server rank or sentinel `8`, and each membership entry is
the ascending list of ranks whose destination is that node, padded on the right
with sentinel `8` to length seven. Compare the resulting fixed-length integer
vectors lexicographically and take the smallest. This includes standby members,
base members, empty sectors, and the designated-server choice and therefore orders
every distinct feasible action in `F_G`. For `F_R`, the same serialization reduces
to the already stated `S1,S2,B` identity ordering because a sector has at most one
targeted agent and that agent is its server.

The registered policy rows are therefore:

| Policy | Action class and objective | Action filtration | Inference vector |
|---|---|---|---|
| `FIXED-RDA` | independent exact expected-`U` indices, decoded in `F_R` | current public `o_t` and known law | realized coupled-tape `(Y,R)` |
| `BEST-RDA` | joint expected-`U` optimum in `F_R` | current public `o_t` and known law | realized coupled-tape `(Y,R)` |
| `GLOBAL-EXACT` | joint expected-`U` optimum in `F_G` | current public `o_t` and known law | realized coupled-tape `(Y,R)` |

For each conclusion world, run each row causally on that world's common realized
demand tape and enter the resulting `(Y,R)` in replicate-level paired inference.
Bellman conditional expectations are solver-verification quantities only and are
never paired against realized executable outcomes. “Ceiling” means optimal
expected `U` within the named current-information policy class, not pointwise
dominance on every realized tape.

The finite one-second lattice, finite demand chain, and six decision epochs make
both problems finite. CM owns the technical choice of exact dynamic program or
equivalent exact formulation; approximation is not a ceiling.

If registered paired inference gives `Better(GLOBAL-EXACT,BEST-RDA)`, the RDA
grammar omits actions useful for the registered `U` objective and no L-RDA
algorithm claim is allowed, regardless of arm ordering. If the single policy
rows satisfy both endpoint `Equivalent` and `ObjectiveEquivalent`, that evidence
concerns only the two selected expected-`U`-optimal rows on this host, horizon,
and panel; it is not equivalence of the complete attainable endpoint frontiers.

## Learning and fresh finite budget

Each of sixteen independent training replicates trains L-RDA and DIRECT-SET on
paired, treatment-blind worlds but independent action-noise tapes. Each learned
arm receives exactly 48 updates of 64 fresh worlds, exactly 32 per training
schedule, or 3,072 one-event physical
trajectories per replicate. The final update-48 checkpoint is the only conclusion
checkpoint. Reporting-only validation cannot select a checkpoint or alter any
field.

Use centralized-training PPO with Adam learning rate `2e-4`, betas
`(0.9,0.999)`, epsilon `1e-8`, no weight decay; joint-action PPO clip `0.15`,
value coefficient `0.5`, entropy coefficient `0.005`, four epochs per update,
one 64-world minibatch per epoch, and global gradient-norm clip `0.7`. Because
each world has one joint post-event trajectory return, there is one state-value
baseline only at the common post-event state `o_0`. There is no per-decision value
target, `gamma`, GAE, reward-to-go, or within-trajectory bootstrap.

Each learned arm has its own state-value critic with parameters separate from its
actor. It uses the same agent- and sector-encoder architectures and input
encodings, agent-embedding sum and mean, both sector embeddings, and the global
fields, followed by an MLP of widths
`128,64,1`. Both critic hidden layers use SiLU and its final scalar value output is
linear. It receives `o_0` only and predicts `U`; it never receives the action.
Every actor or critic linear weight matrix `W` of shape `n_out x n_in` is drawn
independently conditional on its registered `(replicate role, arm,
actor-or-critic, tensor-name)` namespace. If `n_out>=n_in`, draw `Q` from the
Haar-uniform distribution on the Stiefel manifold
`{Q in R^(n_out x n_in): Q^T Q=I_(n_in)}`. If `n_out<n_in`, draw `Q` Haar-uniform
on `{Q in R^(n_out x n_in): Q Q^T=I_(n_out)}`. Set `W=gQ`, with `g=sqrt(2)` for
every hidden linear matrix, `g=0.01` for bid, base-bid, residual-score, and gate
output matrices, and `g=1` for the critic output matrix. All matrix draws are
mutually independent across tensor names, arms, critics, and replicate roles.
Every linear bias is exactly zero.

The DIRECT-SET shared learned base token is exactly 32-dimensional, matching a
sector embedding. It is initialized to the all-zero vector and is trainable
thereafter. There is no other trainable tensor whose initialization is left to
CM or a framework default. The Gaussian scale is the fixed nonlearned `0.30`.
The frozen-initialization checkpoint is deterministic evaluation of these
parameters before the first optimizer step, with means instead of Gaussian draws
and DIRECT's `p_emb=0.5` tie going to its embedded branch.

At data collection, freeze the behavior actor and old critic. For trajectory `i`,
set `A_i=U_i-V_old(o_0,i)`, then standardize the 64 advantages within that arm's
update to mean zero and divide by `max(sample_sd,1e-8)`. Freeze those standardized
advantages for all four epochs. With the arm-specific six-decision trajectory log
probabilities defined above, set
`r_i=exp(logp_new(i)-logp_old(i))` and use the usual negative mean of
`min(r_i A_i, clip(r_i,0.85,1.15) A_i)` as actor loss. Critic loss is the mean of
`(V_new(o_0,i)-U_i)^2`.

For every epoch, `logp_new` is evaluated on the behavior trajectory's recorded
decision states, masks, legal-variable identities, latent bid draws, DIRECT gate
draws, and residual categorical choices. The new policy does not recompute a
different mask or credit variables absent from that recorded decision.

For L-RDA, a decision's entropy is the arithmetic mean of Gaussian entropies over
its legal latent bid variables, defined as zero for an empty set. For DIRECT-SET
it is Bernoulli gate entropy plus
`p_emb` times that embedded-branch mean Gaussian entropy plus `(1-p_emb)` times
the residual categorical entropy (zero when `|F_R|=1`). The trajectory entropy is
the arithmetic mean of the six decision entropies. One Adam optimizer per learned
arm takes one step per epoch on
`actor_loss + 0.5*critic_loss - 0.005*trajectory_entropy`. No loss normalization,
mask term, or credit factor other than those stated here is permitted.

Across two learned arms and sixteen replicates the frozen training program is
98,304 physical trajectories and 6,144 Adam steps
(`16 replicates * 2 arms * 48 updates * 4 epochs`). No imitation,
pretraining, replay from another direction, per-`N` tuning, checkpoint search,
threshold search, or parameter transfer is allowed.

All stochastic laws use counter-based `Philox4x32-10` draws transformed by the
literal distributions stated in this card. Namespace separation is fixed for
replicate, actor initialization by arm, critic initialization by arm, paired
world law, demand, type/roster/tie law, common row permutation, arm-specific
training latent actions, validation worlds, conclusion worlds, and each of the
eight permutation variants. A counter tuple contains the replicate role and the
literal update/world/physical-time/agent-or-edge coordinate as applicable; no
stateful draw order may couple namespaces. The sixteen replicate-role roots and
their concrete integer encodings remain unbound now. Before any construction, CM
must bind them injectively in a fresh manifest without inspecting any prior seed
performance or any outcome; that future administrative encoding cannot alter a
namespace, distribution, coordinate, or panel count.

For every replicate, reporting-only in-support validation has 128 fresh worlds,
64 per training schedule. Conclusion has 128 fresh worlds, 64 per held-out
schedule. Every executable arm receives the identical prehistory state, event,
demand tape, and physical innovation tape; divergent post-action state is a
legitimate mediator. L-RDA-PERMUTE uses its eight within-world derangements.
Both ceilings are computed on every conclusion world. Exact machine seed labels
and world coordinates are deliberately not bound in this definition-only stage.
For competence only, each arm's frozen initialization and final checkpoint are
evaluated deterministically on the exact same validation clones, row permutations,
ties, and exogenous tapes and paired within replicate. Initialization never enters
the conclusion panel.

## Paired observables and inference

For each training replicate, average worlds within each event schedule and then
give join and drop equal weight. The independent inferential units are the sixteen
trained replicates, not individual worlds, decisions, derangements, seconds, or
agents. Define population `B` as the equal-weight conclusion mean of `5->7` and
`7->5`, population `J` as the `5->7` cell alone, and population `V` as the
equal-weight `N<=5` validation mean of `3->5` and `5->3`.
In formulas, `L`, `DIRECT`, `FIXED`, `PERMUTE`, `BEST`, and `GLOBAL` abbreviate
the correspondingly named frozen arm or policy row.

Freeze three disjoint simultaneous families:

1. **Executable claim family:** populations `{B,J}` times contrasts
   `{L-FIXED,L-DIRECT,L-PERMUTE,DIRECT-FIXED}` times endpoints `{Y,R}`: sixteen
   coordinates.
2. **Validation competence family:** contrasts
   `{L_final-L_initial,DIRECT_final-DIRECT_initial}` times endpoints `{Y,R}` on
   population `V`: four coordinates.
3. **Ceiling/grammar family:** populations `{B,J}` times contrasts
   `{BEST-FIXED,GLOBAL-BEST,GLOBAL-FIXED}` times endpoints `{Y,R}`: twelve
   coordinates.

For family `F`, form its `16 replicates x m coordinates` paired-difference matrix
with rows `d_i,F`, and define `theta_F=E[d_i,F]` under the complete abstract
replicate-generating law. Every coordinate is bounded, so the expectation exists.
As a constitutive B4 inferential-model assumption accepted now, before replicate
roots are bound, the sixteen family row vectors are independent and identically
distributed and `d_i,F-theta_F` has a distribution exactly centrally symmetric
about the all-zero vector. This is an assumed statistical-model property, not a
consequence of replicate independence, not a data-dependent gate, and not a
property that may be accepted or rejected after observing any replicate.

Equivalently, under a tested null `theta_F=theta0`, the joint residual-row law is
invariant under every one of the `2^16` transformations that independently
multiplies each complete replicate row by `+1` or `-1`. Under this constitutive
assumption, `theta_F` is both the symmetry center and mean vector and the
null-centered sign-flip inversion below is finite-sample exact. Every interval,
gate, outcome, and maximum claim is explicitly conditional on this inferential
model.

For every candidate vector `theta0`, set `r_i=d_i-theta0`. For each of all
`2^16` sign vectors `e`, apply the same replicate sign to every coordinate. For
coordinate `j`, let `m_j(e)` and `s_j(e)` be the mean and ordinary sample standard
deviation of `{e_i r_ij}` and set `T_j(e)=4*m_j(e)/s_j(e)`. If `s_j(e)=0`, define
`T_j(e)=0` when `m_j(e)=0` and signed infinity otherwise. Set
`M(e)=max_j |T_j(e)|`. With `e_+` the all-positive observed sign vector, define
`p(theta0)=2^-16 * count_e[M(e)>=M(e_+)]`; equality stays in the tail.

The simultaneous `(1-alpha)` family confidence set is the closure of
`{theta0:p(theta0)>alpha}`. Its reported interval for coordinate `j` is the
closed hull of that set's projection onto coordinate `j`, with an unbounded end
reported as infinity. Perform this exact inversion at `alpha=.05` and `.10` for
the simultaneous 95% and 90% intervals. This construction freezes centering,
studentization, zero-variance behavior, shared signs, tie convention, and interval
projection. Any departure from the registered replicate generator is an integrity
failure and makes the family unavailable rather than silently replacing the
prospectively accepted symmetry model with nominal residual bootstrap bounds.
The realized shape of the sixteen rows may not be used to retain, reject, or
replace the prospectively accepted symmetry assumption.

All replicate differences, three family matrices, inversion results, and projected
intervals are reported. Negating an already registered contrast and its interval
supplies the reverse ordering; it does not create another family. No world-level
pseudoreplication, family pooling, post-hoc endpoint choice, or alternative
interval procedure is allowed.

Fresh endpoint materiality margins are `delta_Y=0.03` and `delta_R=0.05`. For
every registered pair of `Y,R` contrast coordinates in full simultaneous
confidence set `C_F^(1-alpha)`, define its projected objective interval

`I_U^(1-alpha) = hull{(theta_Y+theta_R)/2 : theta in C_F^(1-alpha)}`.

This projection uses the full family set, not the Cartesian product of separately
reported coordinate intervals, and adds no testing family. Set
`delta_U=(delta_Y+delta_R)/2=0.04`. Define `ObjectivePositive(a,b)` when the lower
endpoint of the simultaneous 95% `U` interval is strictly above zero, and
`ObjectiveEquivalent(a,b)` when the simultaneous 90% `U` interval lies strictly
inside `[-delta_U,+delta_U]`.

Within a named population and its appropriate family, define:

- `Better(a,b)`: on at least one endpoint, the simultaneous lower bound exceeds
  that endpoint's positive margin, on the other endpoint the lower bound is above
  the negative of its margin, and `ObjectivePositive(a,b)` also holds;
- `Equivalent(a,b)`: simultaneous 90% intervals for both endpoint contrasts lie
  wholly inside their respective `[-delta,+delta]` bands; and
- `NoUsefulGain(a,b)`: simultaneous 95% upper bounds for both endpoints are below
  their positive margins.

Not-significant is never equivalence. Every maximum-claim comparison must satisfy
`Better` separately in both `B` and `J`; a point-estimate sign or a balanced-panel
interval cannot substitute for the `J` interval. Ceiling, support, action, and
association gates for a held-out-roster claim likewise must pass separately in
`J`. Every use of `Better` in competence, headroom, deletion, support, or claim
language includes its objective-positive conjunct. The `7->5` cell can strengthen
a balanced churn statement but never establish post-event execution at `N=7`.

## Frozen identifiability conditions

### Common support

- Every conclusion world is generated and retained without observing any arm or
  ceiling outcome.
- Define support separately for each replicate and learned arm. That arm's
  training collection is every six-decision state it actually encountered in its
  own `48*64` training trajectories, pooling the two registered training schedules
  but not another arm, validation, conclusion, initialization, or ceiling states.
  For every component value actually realized along that arm's deterministic
  final-checkpoint `J` trajectories—type, demand, node/edge, residual travel,
  energy, dwell, age, destination/demand history entry, join/survivor flag,
  cumulative demand, event kind, and feasibility—the identical
  named component value must occur at least once in that same replicate/arm
  training collection. L-RDA supplies the reference for PERMUTE. This is
  component-wise finite-panel recurrence, not joint-vector overlap. `N=7` and its
  unclipped `log(1+N)` scalar are the sole exempt new values. The `7->5` cell has
  prehistory generated at `N=7` and is deliberately not called in-support.
- Every arm starts from the identical cloned state and receives the same future
  exogenous tape.
- In every conclusion replicate and separately in populations `B` and `J`, at
  least 75% of the first five decision states (`t=0,20,40,60,80`) along the
  unpermuted deterministic L-RDA trajectories have two or more free agents in a
  valid permutation block. Every conclusion replicate contains both event cells
  by construction.

Failure makes the affected association or held-out-cardinality contrast
nonidentifying; it is not evidence against either learner.

### Learned competence

On population `V`, each learned arm must satisfy
`Better(final checkpoint, its own frozen initialization)` using the four-coordinate
validation family and, in every replicate, must execute at least two distinct
deterministic feasible assignments in each validation event cell. For every
replicate, along DIRECT's own deterministic final-checkpoint validation
trajectories, clone each pre-action state and compute its embedded-branch and
residual-branch deterministic actions before gate selection. Those actions
must differ on at least 10% of pooled validation decision states, and the
deterministic gate must select the residual branch on at least 5%. These are the
registered material residual-use conditions; mere finite softmax mass is not.
Failure of one learned arm invalidates comparisons that require it but does not
turn the other arm's result into evidence against the failed learner family.

### Headroom and reachability

`Better(BEST-RDA,FIXED-RDA)` must hold separately in `B` and `J` before a learned
failure can be interpreted as unrealized current-information RDA opportunity.
Define **RDA-U-row equivalence** to require both
`Equivalent(BEST-RDA,GLOBAL-EXACT)` and
`ObjectiveEquivalent(BEST-RDA,GLOBAL-EXACT)` separately in `B` and `J`. It is
equivalence only of the two selected expected-`U`-optimal policy rows, not of the
complete attainable `(Y,R)` frontiers of `F_R` and `F_G`. RDA-U-row equivalence
must hold for any positive RDA algorithm claim.

`Better(GLOBAL-EXACT,BEST-RDA)` identifies a registered positive-`U` benefit from
standby/relief actions in the affected population, not bad bidder learning; it
does not characterize every endpoint tradeoff attainable in either grammar.
Because both ceilings are nonanticipating and share executable information, none
of these contrasts contains future-demand clairvoyance.

### Action and association sensitivity

Environmental action sensitivity is measured only on the common treatment-blind
`t=0` conclusion clones, after event and demand transition but before any arm
action. Enumerate every first action in `F_R(o_0)`. For each, use the realized
forty-second demand tape and choose the exact best RDA continuation at `t=20`;
rank distinct first actions by decreasing optimized forty-second demand-weighted
covered seconds, breaking equal values by the registered canonical
complete-assignment tie law. Let `K=|F_R(o_0)|`. If `K<2`, define the
best-versus-second-best gap as exactly zero; that world remains in the denominator
and does not count as action-sensitive. If `K>=2`, let `V_(1),V_(2)` be the values
of the first two distinct ranked assignments and define the gap as
`V_(1)-V_(2)`. In every conclusion replicate and separately for populations `B`
and `J`, at least 25% of all worlds must have a gap of at least ten covered
seconds. No singleton world is excluded or makes the gate unavailable.

Association sensitivity is measured on the first five (`t<=80`) unpermuted
deterministic L-RDA conclusion trajectory states, not on states already changed
by a permuted arm; this leaves a complete forty-second counterfactual horizon. A
**valid association state** is one of those registered states with at least one
free-agent permutation block of size at least two and all required row/handle
mappings available. A missing required mapping makes the complete activity block
incomplete; it may not exclude an otherwise eligible state. States without an
opportunity block remain in the separate 75% opportunity-rate denominator but do
not enter the conditional association-sensitivity pair denominator.

For each valid state `s_t` and variant `k in {0,...,7}`, clone the state and use
the exact independent-block permutation law above to compute variant `k`'s
deranged action on that same unpermuted state. Define two forty-second
counterfactual trajectories on the common realized demand tape. `pi_0` takes the
unpermuted deterministic L-RDA action at `t` and then applies the frozen
unpermuted deterministic L-RDA policy at `t+20`. `pi_k` takes variant `k`'s
deranged action at `t` and then applies that same frozen unpermuted policy at
`t+20` in the state induced by the deranged first action. Both terminate at
`t+40` and use the registered common row permutations, physical clock, masks,
and tie law.

Define raw demand-weighted covered seconds

`C_40(pi;s_t)=integral_t^(t+40) sum_r q_r(u)c_r^pi(u)du`

and `DeltaC_40(s_t,k)=C_40(pi_0;s_t)-C_40(pi_k;s_t)`. Allocation change is one
exactly when the two complete first joint assignments differ. For each replicate
and separately for populations `B` and `J`, give equal weight to every pair
`(s_t,k)` with `s_t` valid and `k in {0,...,7}`. At least 30% of those pairs must
change the allocation and their arithmetic mean `DeltaC_40` must be at least one
raw demand-weighted coverage-second. If the pair set is empty, both association-
sensitivity gates fail. These are opportunity/validity facts, never treatment-
selection filters; all worlds remain in every estimand.

### Precision and integrity

The arm/ceiling action grammar, reachability witnesses, treatment-blind history,
one-event law, complete row mappings, allocator input blindness, ceiling ordering,
and paired world identities must hold. An interval that spans both a positive
materiality boundary and practical equivalence is unresolved. Before the complete
activity block exists, a missing arm, world, event cell, checkpoint, ceiling
rollout, or mapping means that no treatment outcome exists and the unchanged
science returns to CM for completion; incompleteness is not a scientific gate
failure. On a complete block, a scientifically failed gate makes only the
comparisons that require that gate unavailable rather than negative.

For integrity, “ceiling ordering” is the exact Bellman expected-`U` relation
`GLOBAL>=BEST` induced by `F_R subset F_G` at every registered initial state. It
is not a requirement that realized paired `Y` or `R` order on each future tape.

## Complete outcome map

This map is applied only after the complete activity block exists. Apply the
following precedence order; the first satisfied disposition is the single
registered treatment outcome. Every comparison named below must hold separately
in `B` and `J` unless explicitly stated otherwise. Unaffected policy rows may be
reported descriptively when a learner-specific gate fails, but they do not repair
the unavailable learned comparison.

1. **Foundational nonidentifying.** A broken generative law, treatment-blindness,
   clock, action grammar, row mapping, allocator blindness, reachability or
   containment witness, paired-world identity, or exact inferential construction
   makes the whole registered object nonidentifying. No arm ordering is used.
2. **Delete evidence for the RDA action grammar under the registered objective.**
   If valid ceiling inference gives `Better(GLOBAL,BEST)` in either registered
   population, the larger grammar supplies positive registered-`U` value through
   standby/relief actions there. This does not establish a complete endpoint-
   frontier ordering and is not a portfolio action or successor authorization.
3. **No registered U-objective headroom.** If `GLOBAL` is `Equivalent` to FIXED
   and `ObjectiveEquivalent(GLOBAL,FIXED)` holds separately in `B` and `J`, the
   selected GLOBAL expected-`U` row has no registered endpoint or objective
   increment over FIXED. This precedes OR-only but does not exclude a lower-`U`
   policy with a different `Y/R` tradeoff or say anything about another surface.
4. **Delete evidence for the learned bidder formulation.** With RDA-U-row
   equivalence, headroom, common action sensitivity, component support, and both
   learners competent, DIRECT `Better` than both L and FIXED identifies broad
   joint-set learning while disfavoring this learned bidder. “Delete” remains a
   treatment-local evidence statement only.
5. **Bounded learned-RDA value.** RDA-U-row equivalence, headroom, common action
   sensitivity, component support, both-learned competence, and every association
   gate pass, and `Better(L,FIXED)`, `Better(L,DIRECT)`, and
   `Better(L,PERMUTE)` hold. This supports finite-budget value of correctly
   originating-agent-associated reward-trained bids through this allocator.
   Because DIRECT contains L exactly, the advantage is inductive-bias/trainability
   evidence, never expressivity.
6. **Broad learned set-allocation value only.** DIRECT is competent and supported,
   RDA-U-row-equivalence/headroom/action gates pass, and either (a) both learners
   are competent, supported, `Equivalent`, and both are `Better` than FIXED, or
   (b) DIRECT is `Better` than FIXED while L's competence or component support
   fails. Shared
   learned set/history information has value, but no exclusive RDA advantage
   follows. In branch (a), originating-agent association is an additional subclaim
   only if all permutation gates pass and L is `Better` than PERMUTE; branch (b)
   makes no DIRECT-versus-L claim.
7. **Association not identified.** L and DIRECT are competent and supported,
   RDA-U-row-equivalence/headroom/common-action gates pass, and L is `Better` than
   FIXED and DIRECT, but L is not `Better` than PERMUTE, or the explicitly reserved 75%
   permutation opportunity, 30% allocation-change, or one raw demand-weighted
   coverage-second value-loss gate
   fails in `B` or `J`. At most aggregate learned calibration is supported.
8. **OR-only/no learned increment.** RDA-U-row equivalence, headroom, common
   action sensitivity, both-learned competence, and component support pass, while
   L and DIRECT each have `NoUsefulGain` over FIXED. The evidence favors only the
   frozen model-based nonlearned controller on this surface; it does not show that
   learning is useless elsewhere.
9. **Learner-specific nonidentifying or valid unresolved.** A competence or
   component-support failure not assigned by case 6, an unavailable DIRECT
   comparison, a precise mixed ordering, a practical-equivalence gap, a
   value/robustness tradeoff, or a wide interval makes the learned question
   nonidentifying or unresolved. Do not add replicates automatically, tune a
   margin, alter the host, or authorize a successor from that pattern.

## Strongest alternative explanation

The strongest alternative is that the exact current-information, full-horizon
model-based FIXED bidder already captures all useful physical/history structure,
so reward learning adds no allocation information. If learning helps, the
strongest mechanism alternative is generic centralized joint-set learning rather
than an RDA-specific bid interface. If every RDA method remains below
GLOBAL-EXACT, omitted standby, relief, or rotation actions—not bidder quality—are
the principal explanation.

Even a fully positive L-RDA pattern cannot distinguish a particular observed
feature, credit estimator, or learned bid coordinate as the mediator. The
permutation cut supports only originating-agent association of the complete bid
row.

## Maximum claim

The maximum positive claim is:

> In this fixed two-sector, centralized, one-membership-event, 120-second physical
> service toy, a single frozen permutation-equivariant bidder trained only with
> active rosters `N<=5` produced reward-trained, originating-agent-associated bids
> which, through the exact common reward-input-blind-conditional-on-bids RDA
> allocator, improved the registered physical-time task value or forty-second
> post-event robustness, while also having a positive simultaneous lower bound for
> `U=(Y+R)/2`, at the single held-out active roster `N=7` relative to the
> registered full-horizon model-based independently indexed fixed bids and a
> competent equal-information containing learned joint-set policy, under the
> registered materiality, selected-expected-`U`-row ceiling,
> action-sensitivity, support, constitutive symmetry-model, and paired-inference
> conditions.

This claim is finite-budget and panel-specific. It does not establish arbitrary
`N`, repeated churn, a growing task set, decentralized execution or communication,
UAV simulation or deployment, safety, endogenous failure robustness, asymptotic
convergence, global optimality, superior expressivity, or reward blindness of the
learned bidder. `O(N^2)` here means only the fixed-two-task RDA allocation and
DIRECT-SET enumeration paths. It is not a complexity claim for exact policy
ceilings or training, and it is not empirical generalization beyond `N=7`.
Equivalence of the selected BEST and GLOBAL expected-`U` rows does not establish
equivalence of their complete attainable `(Y,R)` frontiers. All statistical
claim language is conditional on the prospectively accepted exact central-
symmetry inferential model.

## Activity boundary and no-rescue rule

Question-relevant activity begins only when one indivisible paired block contains
all information required to evaluate every applicable outcome-map branch:

1. all sixteen final L-RDA and all sixteen final DIRECT-SET checkpoints;
2. both learned arms' complete registered training-state collections and legal
   latent-variable identities needed for component-support assessment;
3. the frozen-initialization and final-checkpoint validation rollouts for both
   learned arms;
4. validation assignment-diversity, DIRECT embedded/residual action-disagreement,
   and residual-branch-selection observations;
5. all conclusion worlds in both held-out schedules;
6. FIXED-RDA, L-RDA, DIRECT-SET, all eight complete L-RDA-PERMUTE rollouts,
   BEST-RDA, and GLOBAL-EXACT outcomes;
7. all row/handle mappings and both physical-time endpoints;
8. every treatment-blind first-action sensitivity calculation;
9. every association-opportunity count, cloned deranged current action, and
   registered forty-second association continuation;
10. the complete executable, competence, and ceiling replicate-difference
    matrices; and
11. the prospectively bound constitutive inferential-model declaration required
    by the exact interval procedure.

The interval inversion itself may be performed deterministically from this
frozen block, but no additional world, rollout, checkpoint, counterfactual
trajectory, support observation, or validation state may be generated after the
activity boundary. Before the boundary, any missing listed item is unchanged-
science completion work and no treatment outcome exists. Training loss, a partial
checkpoint, a feasibility check, a single arm or event cell, source construction,
a unit test, or a ceiling-solver attempt is not question-relevant output.

After activity, a failed scientific gate is interpreted only through the
registered outcome map and cannot be repaired by generating a missing opportunity
or competence observation. No extra replicate, new margin, changed demand law,
alternate fixed bid, wider network, new roster size, action-grammar rescue, or
threshold search can change this treatment. Before activity, implementation,
environment, dependency, solver, serialization, or launcher gaps are CM
engineering work unless CM returns a genuine scientific-definition ambiguity.

## Definition-only CM handoff

CM is asked only for static assessment of this exact revision:

- scientific bindability of every host, clock, observation, arm, action, ceiling,
  metric, inference, and activity definition;
- observability of treatment-blind prehistory, allocator blindness, action
  support, permutation validity, competence, headroom, sensitivity, and ceiling
  ordering without learner/outcome leakage;
- technical feasibility of the containing DIRECT-SET witness, common RDA,
  analytic FIXED-RDA, and exact BEST/GLOBAL ceilings; and
- prospective total construction, training, evaluation, exact-ceiling, wall-time,
  memory, and implementation cost, with any dominant uncertainty stated plainly.

CM must not construct source, run a test or probe, bind a machine seed or world,
create a lease, launch compute, accept runtime, or transfer any VNFC-B1/B3
technical evidence. A missing implementation is cost, not a scientific stop. A
meaning-changing ambiguity returns directly to this EM; a materially changed
prospective total/opportunity cost returns to Root through the stage milestone.
