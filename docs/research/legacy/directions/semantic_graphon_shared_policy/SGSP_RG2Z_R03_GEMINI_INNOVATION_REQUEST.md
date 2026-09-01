# SGSP RIDGEGATE-2Z revision-03 independent Gemini innovation request

You are the divergent scientific innovator for one new definition-only
variable-fleet direction. You have not seen and must not infer any ChatGPT
review. Do not review code, files, runtime, implementation or portfolio
priority. Challenge the physical mechanism, cold-start stress, comparator
fairness, alternative explanations and bounded UAV mapping below. Your answer
is advisory; it cannot close or authorize the object.

## Exact prospective object

```text
direction=semantic_graphon_shared_policy
portfolio_object=SGSP-TARGET-BOUND-TWO-ZONE-DEFINITION
revision=SGSP-RG2Z-SCIENCE-20260815-03
task=RIDGEGATE-2Z
definition_only=true
result_blind=true
empirical_activity_authorized=false
```

Every packet copy retains its originating event time through duplication,
transfer and retransmission, and FIFO age is always measured from that origin.
Composite answerability ranges only over the two trained arms, never the
uniform competence floor. The nonretention branch reports only prospectively
registered failed-qualification predicates or interval-defined equivalence/
superiority relations; it does not infer a negative mechanism claim merely
because a positive gate fails.

`RIDGEGATE-2Z` is a 12-slot cooperative two-basin surveillance/relay toy with
stable public roles `WEST-SURVEYOR`, `EAST-SURVEYOR`, `RIDGE-RELAY`. Balanced
fleets train one shared recurrent policy at `N={9,15}` and deploy it unchanged
at held-out `N={6,21}`. Role multiplicities therefore change from seen `3,5`
to held-out `2,7`; no roster-specific adaptation or normalization is allowed.

Each basin has exactly three event times sampled from slots `0..7`. Surveyors
detect a local event with probability `0.75` only on `SCAN`; detected reports
expire before `event_time+4`. Surveyors choose scan/uplink/hold. Half-duplex
relays choose which basin to listen to, forward to base, or hold. Surveyor and
relay FIFO capacities are two and four. A report scanned at `t` cannot uplink
until `t+1`; unit-latency uplink and forwarding make its fastest base delivery
`t+3`.

Simultaneous surveyor uplinks in one basin collide completely. With exactly
one sender, every relay listening to that basin decodes independently at the
declared load-adjusted physical probability. Simultaneous relay forwards also
collide completely; a unique forward uses a separately declared load-adjusted
base link. There is no capture. Failed packets remain FIFO heads for
retransmission; decoded reports are acknowledged. The base scores only the
first timely arrival of an event ID.

Return is

```text
J=0.65*(D_W+D_E)/6 + 0.25*min(D_W,D_E)/3 + 0.10*(1-WASTE),
```

where waste is the fraction of uplink/listen/forward actions that create no
role-appropriate nonexpired enqueue or no new timely distinct base delivery.
Reward never queries a policy kernel or learned state.

The public physical prior is frozen before reward, events or learning:

```text
P0 = [[0.92,0.48,0.88],
      [0.48,0.92,0.82],
      [0.86,0.78,0.90]]
L  = [[1,2,1],
      [2,1,1],
      [1,1,1]]
p_ab(n_b)=logistic(logit(P0_ab)-0.22*(n_b-1))
K0_ab(n_b)=p_ab(n_b)/L_ab.
```

The relay-receiver/surveyor-sender entries drive mission uplink physics; the
separate base law is

```text
p_BASE(n_R)=logistic(logit(0.90)-0.22*(n_R-1)), latency=1.
```

Other `P0/L` entries define only the public policy prior. The simulator never
queries `K0` or learned residuals. Agents exchange one noiseless fixed-width
status vector per slot on an abstract matched policy bus that carries buffer
ages/counts but no report payload or event ID and does not consume mission
half-duplex radio.

Both learned arms use the same message encoder, GRU actor, team critic, legal
support, 18 output-connected edge coefficients, initialization, optimizer,
rollouts, communication and useful work. For role multiplicity `n`,

```text
v(n)=(2*log(n)-log(14))/log(7/2)
r_ab(n)=beta_ab0+beta_ab1*v(n)
omega_ab(n)=K0_ab(n)*exp(r_ab(n)).
```

`PHY-TRUST` projects beta into `[-0.15,+0.15]`; `EDGE-FLEX` performs the same
operation into `[-1.50,+1.50]`. Both start at beta zero and the identical
complete policy. The narrow family is a literal strict subset; EDGE receives
the same physical baseline/counts/messages and differs only in reachable
residual range.

There is one trainer and budget: centralized Monte-Carlo actor-critic, one
full-batch projected-Adam step for 64 fresh 12-slot episodes per update, 32 at
each training roster, for exactly 512 updates. Only the immediate update-512
checkpoint is evaluable. Arms use identical initialization and stable arm-
independent potential-outcome addresses for worlds, detections, packets and
action uniforms. A future empirical object would use 24 fresh training seeds
and 256 fresh evaluation episodes per roster/seed; no numeric run coordinates
are authorized here.

EDGE must beat a legal-uniform task floor at both training sizes and be
practically equivalent to PHY there. The retain branch then requires at both
held-out sizes: PHY-minus-EDGE return above `0.04`; held-out-minus-seen
advantage above `0.03`; worse-basin delivery advantage above `0.02`; and an
action-sensitive same-cut mechanism.

The cut cyclically rotates the physical sender-role columns for each arm while
holding residual indices, messages, actor, simulator, reward, legal support
and potential outcomes fixed. Treatment legal-action TV must exceed `0.08`,
treatment return loss `0.05`, and differential attenuation

```text
I=(J_PHY,int-J_EDGE,int)-(J_PHY,rot-J_EDGE,rot)
```

must exceed `0.03`. Composite per-held-out-size endpoint-interiority/action-
support scalars exclude score-endpoint saturation for direct return, cold-start
interaction, worse-basin delivery, cut return and attenuation, and require the
legal-action simplex to permit TV above its margin before efficacy branches are
read. They do not claim a global oracle attainable-return envelope. Invalid,
saturated or comparator-incompetent panels are non-identifying.
Every other valid, answerable complete panel with competent EDGE does not
retain the fixed prior as default for this task/budget. No wrong-center arm,
budget search or old result can enter a branch.

The maximum positive claim is only a useful action-sensitive physical-kernel
inductive bias at this one budget and the two adaptation-free held-out rosters
on this toy. It is not kernel truth, a learning rate/curve, arbitrary terrain,
churn, field-radio robustness or UAV efficacy.

## Independent innovation questions

1. Is the ridge-shadow/half-duplex packet mechanism physically coherent enough
   to be a non-artificial target-bound toy? Identify any self-fulfilling use of
   the physical table, reward leakage, implausible collision/load law or public
   information.
2. Does moving role multiplicity from `3,5` to `2,7` create a meaningful
   cold-start coordination stress, or only a count-normalization exercise?
3. Is the wider residual-box EDGE family genuinely competent and
   non-handicapped despite starting from the same physical baseline? Identify
   any hidden optimization, information, support, communication or work
   asymmetry.
4. Does rotating both arms make differential attenuation scientifically
   informative, or can the same statistic be driven by generic OOD damage?
5. Give the strongest physical or learning explanation that could mimic a
   qualifying positive without establishing semantic-prior value.
6. Propose at most one concrete revision that materially improves causal
   information without adding a second budget, wrong-center arm, new surface,
   UAV production or empirical activity.
7. State whether the toy-to-UAV mapping is credible at the bounded claim level
   and list the most important exclusions.

## Required response format

```text
INNOVATION_DISPOSITION=KEEP|REVISE|ABANDON

PHYSICAL_COHERENCE
<analysis>

COLD_START_MECHANISM
<analysis>

EDGE_FAIRNESS
<analysis>

SYMMETRIC_CUT
<analysis>

STRONGEST_COUNTEREXPLANATION
<analysis>

ONE_HIGH_VALUE_REVISION
DISPOSITION=NONE|ONE_REVISION
<if one, exact change and why>

TOY_TO_UAV_BOUNDARY
<credible mapping and exclusions>

FINAL_ADVISORY
<concise direction-local recommendation; no portfolio choice>
```
