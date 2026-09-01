# RISP-B3 target-bound tracking/relay ChatGPT External Pro closure request

```text
direction_id=renewal_indexed_score_plasticity
candidate=RISP-B3-TRG
science_revision=RISP-B3-TRG-SCIENCE-20260815-01
named_target=TRI-SECTOR-DELAYED-ACK-TRACK-RELAY
request_kind=SAME_CONVERSATION_MATHEMATICAL_AND_CAUSAL_CLOSURE
provider_role=ChatGPT External Pro
conversation_relationship=continue_existing_RISP_direction_conversation
scientific_activity_started=false
```

This is a new target-bound definition, not a revision or rerun of RISP-B2.
RISP-B2 remains complete and immutable. Please determine whether the exact
prospective object below is mathematically and causally closed before any
source, coordinate, test, training, evaluation, or compute exists. Do not
review code or choose portfolio priority.

## Target and external-k question

Two parameter-sharing, noncommunicating agents independently track a moving
target sector and relay a packet to a recipient. Actions are three held relay
beams `(LEFT,CENTER,RIGHT)`. Episodes last `T=192` ticks. At boundary `tau_n`,
the controller observes only `[tau_n/T,k_n/12]`, selects `a_n`, and holds it for
the externally imposed `k_n` ticks.

The hidden sector moves every tick independently of action:

```text
P(stay)=23/24; P(each other sector)=1/48.
```

Write `P_k=P^k` and `lambda=15/16`. At hold completion, hidden sector
`c_(n+1)~P_k(c_n,.)`, then the recipient ACK satisfies

```text
P(Y=+1 | a=c_(n+1))=4/5
P(Y=+1 | a!=c_(n+1))=1/5.
```

The hold's physical utility is `kY`. ACK and utility become controller-available
only at completion. The completion sector becomes the next boundary sector.
After every nonterminal completed hold, ACK may update private state before the
next duration is latched and before the next legal action. The action does not
move the target; there is no mid-hold update, future duration, hidden-sector,
future-reward, other-agent, or unchosen-outcome input.

One shared controller trains jointly at fixed `k={4,8}` and freezes. The same
parameters evaluate at held-out `k=12`, `4->12`, and `12->4`, with no per-`k`
head, gain, checkpoint, reset, or evaluation optimizer. Switches occur at
`t=96`; post-switch windows exclude the first new-duration hold:

```text
Q(12):    ticks 0,...,191
Q(4->12): ticks 108,...,191
Q(12->4): ticks 100,...,191.
```

For window `W`, `Q=(1/(2|W|))*sum_i sum_(holds fully in W) kY`, and
`Q_TARGET` is the equal-weight mean of the three schedule values within seed.

## Common direct policy and frozen G

The slow policy is a common bounded MLP from `[tau/T,k/12]`. Each agent has
private simplex state `q_0=(1/3,1/3,1/3)` and acts from

```text
pi(a|o,q)=0.5*pi_slow(a|o)+0.5*q(a).
```

For finite rational `r`,

```text
z_j=6r_j/(6+|r_j|)
omega_j=16+(z_j+6)^2
Affinity(r)_j=omega_j/sum_l omega_l.
```

Every action remains above `1/21`. The recurrence packet after a completed ACK
is

```text
phi=[1,q(LEFT),q(CENTER),q(RIGHT),onehot(a)[3],Y,
     Y*onehot(a)[3],k/12,tau/T].
```

The fixed raw semantic map is

```text
g(+1,a)_j=+30 if j=a else -30
g(-1,a)_j=-30 if j=a else 0.
```

The unique finite binary64 `3x13` matrix `G`, zero outside the two categorical
action blocks, satisfies `G phi=g(Y,a)`. With a uniform completion-sector
prior, ACK posteriors are `(2/3,1/6,1/6)` after success and
`(1/9,4/9,4/9)` after failure in selected-action order. At uniform slow/state,
the next-policy TV changes are `40/171` and `35/363`. For next hold duration
`k`, exact offline value is

```text
V_k(b,pi)=sum_a pi(a)*[-3/5+(6/5)*(b P_k)(a)],
```

and local G gains over no update are

```text
DeltaV_G(+1,k)=(8/57)*(15/16)^k
DeltaV_G(-1,k)=(14/363)*(15/16)^k.
```

Both are positive for every registered duration. This is a local structural
certificate, not a physical-time success route.

## Equal-function-class learned arms

```text
TRACK-G-ANCHOR: q_(n+1)=Affinity(E_A phi_n), E_A starts/decays about G
TRACK-CONTAIN:  q_(n+1)=Affinity(E_C phi_n), E_C starts/decays about 0.
```

Each `E` contains the same 39 learned binary64 scalars and ranges over every
finite binary64 `3x13` matrix. Both arms have the same slow network,
initialization tape, packet, head, action support, loss, batch order, AdamW
work, update count, update opportunities, and reset law. Only the declared
initialization and centered-decay prior differ. No old checkpoint, seed, random
word, optimizer state, partial value, or coordinate is reused.

Training has sixteen prospective seed strata. Each arm receives 512 AdamW
updates, batch 16 complete episodes alternating eight `k=4` and eight `k=8`.
AdamW uses `lr=3e-4`, betas `(0.9,0.999)`, epsilon `1e-8`, global clip `1`,
and centered recurrent decay `1e-4`. Final update 512 is fixed.

The common physical-reward policy loss uses the exact controller-history
belief baseline. If `mu=beta P_k`, then `EY=-3/5+(6/5)mu(a)` and
`delta=kY-k sum_a pi(a)EY(a)`. The auxiliary loss is exact cross-entropy from
`q_(n+1)` to `v(Y,a)=Affinity(g(Y,a))`. Its prospective weight is `1` in both
arms. It uses only completed ACK and selected action. No checkpoint or early
stop is selected.

## Integrated, non-standalone G exploitability gate

The same complete panel includes `CONTAIN-G-BOUND`: clone the final containing
slow checkpoint, ignore learned `E_C`, and use exact `G` at evaluation with
actual completed ACKs. It is inseparable from this target/value panel and
cannot be run or claimed alone.

The same slow checkpoint has three outcome-independent controls:

```text
NO-RECURRENCE: q_next=q
FIXED-PERSIST: q_next=v(+1,a), ignoring Y
GLOBAL-RATE:   p0=2/5;
               q_next=Affinity(p0*g(+1,a)+(1-p0)*g(-1,a)), ignoring Y.
```

Within seed/schedule, `Q_C,BEST` is the maximum of these three prospectively
named control values. `CONTAIN-G-BOUND` must, at each seen schedule separately
and on the equal-weight target mixture, clear all of:

```text
lower95(Q_G- Q_C,BEST)>0.02
seen lower95(ORACLE-Q_G)>0.02
lower95 fraction(TV_update>=0.01)>0.25
lower95 fraction(DeltaV_update>0)>0.55
lower95 mean(DeltaV_update)>0.005.
```

If any gate fails, the controlling branch deletes completed-ACK recurrence
from this named target/controller/package and forbids a standalone transplant,
sign-reversed center, or bridge from that outcome. If all pass, interpretation
immediately continues to the already computed matched value cells in the same
complete panel.

## No-lineage and fixed/global controls

Each learned checkpoint has `INTACT`, `MARGINAL-TWIN`, `NO-RECURRENCE`,
`FIXED-PERSIST`, and `GLOBAL-RATE` cells. The twin maintains exact belief
`rho_n` over the hidden sector from its controller-visible history. Before the
ACK, `mu=rho_n P_k` and

```text
pbar=1/5+(3/5)mu(a).
```

It draws an independent sign with this probability and feeds only that sign to
the recurrence. Actual ACK still scores the environment, but is never read by
the twin. Because the twin sign is independent of the actual sector/ACK given
history, `rho_(n+1)=rho_n P_k`. This preserves the one-step conditional ACK law
and update opportunity while severing realized recipient lineage.

`UNIFORM` and a current-sector `STATE-ORACLE` are qualification controls. The
oracle still faces target drift during the hold. Every evaluation cell has 64
episodes per seed/schedule and paired abstract event tapes. The complete panel
contains 13 cell families: ten learned-architecture cells, `CONTAIN-G-BOUND`,
uniform, and oracle. Concrete RNG coordinates remain unbound.

## Qualifications and interpretation

Only the complete 16-seed/five-schedule/13-cell panel is interpretable. After
the G gate, both learned intact arms must, on each seen schedule separately,
have lower95 physical value above their within-seed best no-recurrence/fixed/
global control by `0.02` and oracle headroom by `0.02`. Each arm must also, on
each seen schedule and the target mixture, clear the same TV, positive-DeltaV,
and mean-DeltaV gates as G. A failure is nonidentifying, not efficacy or harm.

Seed-first target estimands are

```text
D_I=Q(A,I)-Q(C,I); D_M=Q(A,M)-Q(C,M); PSI=D_I-D_M
C_A=Q(A,I)-Q(A,M); C_C=Q(C,I)-Q(C,M)
R_A=Q(A,I)-Q(A,BEST); R_C=Q(C,I)-Q(C,BEST).
```

Use one-sided 95% `t` bounds over sixteen seeds, two-sided 90% equivalence
intervals, schedule-wise 98.333% nonharm, and a four-member 98.75% harm family.
After invalidity, G-gate, and learned-arm qualification precedence, branches
are:

1. `NAMED_TARGET_RECURRENCE_DELETED_G_UNEXPLOITABLE`: any G gate fails.
2. `G_EXPLOITABLE_BUT_MATCHED_VALUE_NONIDENTIFYING`: G passes but either
   learned arm fails qualification.
3. `NAMED_TARGET_G_CENTERED_TREATMENT_HARM`: pooled `D_I` upper98.75 below
   `-0.02`, any schedule upper below `-0.03`, or `R_A` upper below `-0.02`.
4. `TARGET_EXTERNAL_K_REALIZED_ACK_G_PRIOR_SUPPORTED`: lower95
   `D_I>0.02`, `PSI>0.015`, `C_A>0.015`, `R_A>0.02`, `R_C>0.02`;
   `D_M` 90% inside `[-0.01,0.01]`; all schedule `D_I` lower bounds above
   `-0.01`.
5. `TARGET_DIRECT_RECURRENCE_VALUE_WITHOUT_G_PRIOR_SPECIFICITY`: lower95
   `R_A,R_C>0.02`, `C_A,C_C>0.015`; `D_I,D_M,PSI` 90% intervals all inside
   `[-0.01,0.01]`.
6. `TARGET_NO_REALIZED_LINEAGE_OR_FIXED_GLOBAL_ALTERNATIVE_COMPATIBLE`: either
   both intact-minus-twin intervals are inside `[-0.01,0.01]` and both twins
   qualify, or `Q(A,I)-Q(A,BEST)` is equivalent within `[-0.01,0.01]` and the
   best-control composite clears physical competence/headroom. Delete only the
   lineage claim and move toward the named sufficient alternative.
7. `NO_REGISTERED_MINIMUM_G_PRIOR_VALUE`: no harm and upper95 `D_I<=0.02`,
   `PSI<=0.015`; delete only those minimum prior/interaction claims.
8. `VALID_UNRESOLVED`.

The strongest live alternative after a favorable branch is generic shifted
initialization/centered decay, alignment-loss geometry, conditioning, or slower
finite convergence, plus fixed selected-action persistence, global ACK rate,
target autocorrelation, and conditional marginal ACKs. The exact maximum claim
is the finite named two-agent target, package, held-out duration, and switches
only. No arbitrary `k`, convergence, variable `N`, coordination, real-UAV,
safety, or deployment statement is permitted.

## Closure requested

Return exactly one leading disposition:

```text
CLOSED
```

if the complete object has no remaining mathematical, causal, comparator,
qualification, branch-map, or claim-boundary defect, or

```text
REVISION_REQUIRED
```

followed by every exact science-bearing defect and corrected condition.

Please explicitly decide:

1. whether the delayed-ACK event order and target-motion model support the
   claimed completed-recipient causal path without future leakage;
2. whether `CONTAIN-G-BOUND` is genuinely decision-necessary and inseparable
   from the matched value object, and whether its negative deletion is bounded
   correctly;
3. whether the learned arms are literally function-equivalent and the
   no-lineage/fixed/global controls rule out the named alternatives;
4. whether the physical endpoint, competence/action/value gates, inference,
   and branch precedence are jointly executable without an outcome-changing
   choice or contradictory branch; and
5. the strongest remaining alternative and exact maximum claim.

Do not authorize source, construction, tests, probes, coordinates, training,
evaluation, compute, an old-object rerun, a standalone transplant, or a
sign-reversed center.
