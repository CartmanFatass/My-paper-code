# DISH RBHR r05 treatment, comparators and executable certificate

```text
document_kind=direction_science_treatment_comparator_certificate_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-05
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
stage=definition-only
science_activity_authorized=false
successful_handover_limit_per_trajectory=1
```

This file fixes controller authority, message cadence, handover logic, the
certificate and literal FLEX containment. All five learned arms use the same
observation and full tensor graph; masks below change only the named behavior.

## 1. Controller copies and physical authority

For each physical vehicle `i in {0,1}`, maintain weight-tied recurrent states
`h_i^I,h_i^S in [-1,1]^128`, all initialized to the zero vector at tick `-1`.
All four states update on every live primitive
tick from the same shaped causal observations and their role bits. Let `o_n` be
the unique service owner and `s_n=1-o_n`.

Before a successful commit:

```text
applied_motion(o_n)=P_n(A_theta(h^I_{o_n}))
applied_motion(s_n)=P_n(A_theta(h^S_{s_n})).
```

Only `h^I_{o_n}` may originate a scored SERVICE_RELAY. `h^S_{s_n}` drives the
standby's motion, snapshot assimilation and readiness messages, but no scored
payload. The two other copies compute for matched graph cost but cannot actuate,
send a scored payload or affect the arbiter. This mapping applies to
STRUCTURED, FLEX, NEVER, IMMEDIATE-ELIGIBLE and FIXED-HYSTERESIS.

At an ordinary renewal `n`, a legal intent is transmitted during tick `n` and,
if delivered, proposes a compare-and-swap at the start of tick `n+1`. The old
owner remains exclusive through tick `n`; a successful new owner is exclusive
from tick `n+1`. At that boundary the transaction moves

`(owner,service_epoch,next_payload_sequence,handover_used)`

atomically, increments `service_epoch`, preserves both UAV SOURCE buffers and
the base buffer, and sets `handover_used=1`. The prepared standby copy is
promoted:

```text
h^I_{s,+}=P_h(alpha*h^S_{s,-}+(1-alpha)*h^I_{o,-})
h^S_{o,+}=h^I_{o,-}; h^S_{s,+}=h^S_{s,-}; h^I_{o,+}=h^I_{o,-},
P_h(x)=componentwise_clip(x,-1,1).
```

STRUCTURED and both simple rules use `alpha=1`. The former owner is demoted at
the same boundary. Every later transfer is ineligible in every arm and branch.
Revision 05 permits at most one successful handover per episode in every
STRUCTURED, FLEX, simple-rule and fork trajectory.

## 2. Complete deployed controller function

### 2.1 Partner channel and ordered observation

Every live tick each physical UAV sends the charged `64-byte STATE` packet

```text
(sender_tick,p_x,p_y,v_x,v_y,a_x,a_y,B,camera_missing,
 responder_margin,base_margin,owner_bit,service_epoch,k_epoch,D,G1,G5,integrity).
```

It arrives one tick later under inter-UAV radio physics. Each receiver keeps the
newest delivered sender tick. There is no base acknowledgement or other partner
channel.

For copy type `c in {I,S}` on physical UAV `i`, the actor observation is the
following ordered 54-vector in global reflected world axes. Continuous values
are in the displayed physical units and are normalized by section 2.5;
Boolean/one-hot values are not normalized.

| indices | values and units | causal source / absent sentinel |
|---:|---|---|
| 1–2 | `is_I,is_S` | fixed copy one-hot |
| 3–4 | `self_is_owner,handover_used` | current arbiter bits |
| 5–6 | `p_i.xy-b.xy` metres | current local navigation |
| 7–8 | `v_i.xy` m/s | current local navigation |
| 9–10 | held `a_i.xy` m/s^2 | current actuator state |
| 11 | `B_i` joules | current battery |
| 12–15 | camera-present, camera position minus `p_i` (2 m values), camera-missing | current camera; position is `(0,0)` when absent |
| 16–19 | camera-filter position minus `p_i` (m), velocity (m/s) | current physical-vehicle filter |
| 20–22 | filter `P_xx,P_xy,P_yy` in m^2 | current position-covariance block |
| 23–25 | responder, base and partner radio margins (dB) | current physical link measurements |
| 26–27 | SOURCE-buffer present, age seconds | current local header; age `1e6` if absent |
| 28–29 | partner STATE present, age seconds | newest delivered STATE; age `1e6` if absent |
| 30–31 | partner `p-p_i` metres | STATE; `(0,0)` if absent |
| 32–35 | partner velocity and held action | STATE; four zeros if absent |
| 36–38 | partner battery joules, camera-missing, owner bit | STATE; three zeros if absent |
| 39–41 | current `k` one-hot for 4,8,12 | public renewal controller |
| 42–44 | `k_epoch,c[n],RENEW[n]` | public renewal controller |
| 45–47 | `D,G1,G5` | current local values on the owner; on the other UAV, values from the newest delivered owner STATE, all zero if absent |
| 48–49 | prepare latch, warmup ticks clipped at 20 | local protocol state |
| 50–51 | accepted SNAPSHOT present and age ticks | local buffer; age `1e6` if absent |
| 52–53 | delivered READINESS present and age ticks | local buffer; age `1e6` if absent |
| 54 | current header-version match | deterministic arbiter predicate |

Absolute tick, remaining horizon, opaque SOURCE body, true package/stratum,
future clocks/noise and RNG identity are absent.

For row 54, an I-copy's `header-version match` is one iff a delivered READINESS
and its referenced accepted SNAPSHOT exist; current owner, service epoch,
common SOURCE sequence and `k` epoch match both records as applicable; and the
current pre-reservation `next_payload_sequence` equals only the newest matching
READINESS record's own post-reservation sequence. It is not compared with the
older accepted snapshot's historical next-sequence field. An S-copy's value is
one iff its accepted SNAPSHOT exists, its owner/service epoch/common SOURCE/
`k` fields still match current protocol state and both SOURCE buffers retain
the named common lineage. Its accepted snapshot next-sequence field was checked
only at acceptance and is historical afterward. Either value is zero for an
absent or stale record. These deterministic checks expose no opaque SOURCE
contents.

### 2.2 Encoder, GRU and head authority

For normalized observation `o`,

```text
e=tanh(W2*tanh(W1*o+b1)+b2)
z=sigmoid(Wz*e+Uz*h_prev+bz)
r_g=sigmoid(Wr*e+Ur*h_prev+br)
h_tilde=tanh(Wh*e+Uh*(r_g elementwise h_prev)+bh)
h=(1-z) elementwise h_prev+z elementwise h_tilde.
```

All encoder/GRU widths are 128; this displayed update convention is the only
GRU convention. The motion head is linear from the physically authoritative
copy: owner motion from `h_o^I`, standby motion from `h_s^S`. The prepare
Bernoulli comes only from `h_o^I`. The commit Bernoulli, service probabilities
and FLEX residuals come only from `h_s^S`. The four-state prediction head runs
on both `h_o^I` and `h_s^S`. Link/missing auxiliary heads run on every copy for
its attached physical vehicle. Non-authoritative copies have no behavioral
head authority.

The global raw-motion log-standard-deviation vector has exactly four ordered
components `(owner_x,owner_y,standby_x,standby_y)`. Each motion head emits the
raw mean `m`; training samples the pre-projection `y` defined in section 5,
while evaluation sets its `xi` to zero. Projection occurs only after likelihood
sampling.
Linear-head output dimensions are: motion 2, prepare logit 1, commit logit 1,
target-state mean 4, target Cholesky 10, service logits 20, link means 2, link
raw standard deviations 2, camera-missing logit 1, and FLEX
`DeltaI/alpha/r/beta` raw outputs `128/1/1/1`. Every head bias is zero at
initialization; only the four FLEX head matrices/biases are forced exactly zero.

### 2.3 Exact control-message schemas and snapshot assimilation

Fields are serialized in the listed order; unused padding is zero and is not a
policy input. Continuous values are little-endian IEEE-754 float32; tick and
sequence fields are little-endian uint32; epochs uint16; IDs, booleans and
reason codes uint8; integrity is one uint32. The remaining bytes to the fixed
wire size are zero.

Owner/epoch/sequence/lineage/`k` version headers are stamped and checked by the
deterministic token arbiter from causal protocol metadata. This does not expose
those header values to a learned observation except where the 54-vector
explicitly lists them.

```text
SNAPSHOT, 96 bytes:
  owner_id,service_epoch,post_reservation_next_payload_sequence,
  common_SOURCE_sequence,k_epoch,snapshot_tick,
  owner four-state prediction mean,
  ten upper-triangle elements of its symmetric 4x4 covariance,
  owner base/responder margins,owner raw boundary-action mean x/y,integrity.

READINESS, 48 bytes:
  sender_id,accepted_snapshot_owner,readiness_tick,accepted_snapshot_tick,service_epoch,
  post_reservation_next_payload_sequence,common_SOURCE_sequence,k_epoch,Q95,d_M^2,
  final standby candidate raw mean x/y,commit_probability,integrity.

COMMIT_INTENT/NOOP_INTENT, 32 bytes:
  origin_tick,bound_readiness_tick,old_owner,new_owner,service_epoch,
  post_reservation_next_payload_sequence,common_SOURCE_sequence,k_epoch,
  origin_certificate_pass,request_transfer,integrity.

COMMIT_RESULT, 24 bytes:
  application_tick,success,reason_code,owner_id,service_epoch,
  next_payload_sequence,k_epoch,integrity.
```

`reason_code` is the first false application predicate in the order displayed
in section 5.4, or zero on success. Every integrity field is the first four
bytes of `SHA256(all preceding serialized message bytes)`. The sender always
generates it correctly and the channel has no bit corruption, so an attempted
message is usable exactly when its physical margin delivers it and the
deterministic check matches.

For FLEX, the READINESS `Q95` field carries the adjusted `Q_F` value and its
`commit_probability` is `sigmoid(ell_commit+4r)`; the other arms carry the
unadjusted values. Every displayed decoded float is the exact float32 value
used by the receiving predicate.

The ten prediction-Cholesky outputs are ordered exactly

`(l00,l10,l11,l20,l21,l22,l30,l31,l32,l33)`

and form the rowwise lower triangle

```text
L=[[l00,0,0,0],
   [l10,l11,0,0],
   [l20,l21,l22,0],
   [l30,l31,l32,l33]].
```

Apply `softplus(raw)+1e-3` exactly to `l00,l11,l22,l33`. The ten serialized
symmetric-covariance entries are ordered exactly
`(P00,P01,P02,P03,P11,P12,P13,P22,P23,P33)`. The snapshot encoder, float32
wire, reconstruction, propagation and auxiliary target loss all use this same
order.

Define ordered snapshot encoder input

```text
x_snapshot=(prediction_mean_0..3,covariance_upper_triangle_0..9,
 owner_base_margin,owner_responder_margin,
 owner_raw_boundary_action_mean_x,owner_raw_boundary_action_mean_y).
```

Thus `x_snapshot` has exactly eighteen continuous components. All wire owner,
epoch, sequence, lineage, `k` and tick headers remain deterministic-arbiter
metadata and never enter this learned encoder. Normalize only those eighteen
fields with the dedicated snapshot statistics in section 2.5 and apply
`e_snap=tanh(W_snapshot*x_snapshot+b_snapshot)`, where `W_snapshot` has shape
`128 x 18`. On first accepted snapshot compute with `W_bridge` of shape
`128 x 256`

`h_bar=tanh(W_bridge*concat(h_s^S,e_snap)+b_bridge)`.

On the first accepted-snapshot tick `n`, evaluate
`u_I[n]=W_DeltaI*h_s^S[n-1]+b_DeltaI` from the pre-assimilation previous-tick
standby-shadow recurrent state, then set
`DeltaI[n]=0.25*tanh(u_I[n])`. Form `h_bar` from that same pre-assimilation
state and `e_snap`. STRUCTURED installs `h_prev=P_h(h_bar)` and FLEX installs
`h_prev=P_h(h_bar+DeltaI[n])`; that tick then executes exactly one displayed
GRU update with input `e_snap`. `DeltaI` is not recomputed from `h_bar` or the
post-update state. Later accepted snapshots do not reinitialize: `h_prev` is
the existing state and `e_snap` replaces the ordinary observation embedding
for that tick's standby-shadow update. Every other copy uses its ordinary
embedding. No other message directly edits recurrent state.

At every READINESS emission tick `r`, evaluate `alpha[r]`, readiness residual
`r[r]` and `beta[r]` from the post-GRU standby-shadow state `h_s^S[r]`. The
zero-residual STRUCTURED embedding remains unchanged.

### 2.4 Centralized critic vector

The critic input is an ordered causal-current vector:

1. responder `(g_x,g_y,gdot_x,gdot_y)`;
2. for physical UAV 0 then 1: `(p_x,p_y,v_x,v_y,a_x,a_y,B,
   camera_present,camera_x,camera_y,camera_missing,
   responder_margin,base_margin,partner_margin,
   SOURCE_present,SOURCE_age,SOURCE_sequence,owner_bit)`;
3. base-buffer `(present,age,position_error,first_margin,second_margin)`;
4. token `(owner_0,owner_1,service_epoch,next_payload_sequence,handover_used)`;
5. renewal `(k4,k8,k12,k_epoch,c,RENEW,pending_switch)`; and
6. `terminal`.

Missing camera coordinates are zero; absent packet age/error are `1e6`, absent
margins `-1e6`, and absent sequence zero with its present bit false. The critic
has two 128-unit tanh layers and a scalar output. It receives no future state,
package/stratum label, counterfactual, RNG identity or remaining horizon and is
unused at deployment.

### 2.5 Normalization state

Actor, snapshot-encoder and critic continuous dimensions have separate per-arm Welford states,
initialized `count=0,mean=0,M2=0`. For `count<2`, variance is exactly one;
otherwise use unbiased `M2/(count-1)`. Normalize as
`(x-mean)/sqrt(variance+1e-8)` and clip to `[-10,10]`. Present bits protect all
sentinels: an absent continuous entry is excluded from Welford updates and its
post-normalization value is forced to zero. Boolean/one-hot fields pass
unchanged. Statistics update only under
the training-order rule and freeze after update 1,024.

## 3. Causal degradation and preparation clocks

The common deployable Boolean is

`D[n]=1{current owner camera is missing OR current owner-to-base margin<6 dB}`.

It is independent of the hidden regime and `tau_d`. From reset define

```text
G1[n]=max_{0<=j<=n} D[j]
G5[n]=1 iff at least one run D[j]=...=D[j+4]=1 ends by n.
```

STRUCTURED, FLEX, NEVER and IMMEDIATE use `G1`; FIXED-HYSTERESIS uses `G5`.
The simple rules therefore require respectively at least one indicator tick or
five consecutive primitive indicator ticks. No evaluator onset enters either
rule.

At an ordinary renewal after its applicable latch is true:

- STRUCTURED, FLEX and NEVER latch preparation only if their sampled/evaluation
  prepare bit is one;
- both simple rules latch preparation unconditionally; and
- once latched, preparation persists to handover, terminal or episode end.

A `k` switch does not reset a recurrent state, filter or warmup clock, but it
invalidates a stored certificate until a snapshot bearing the new `k` epoch is
accepted.

## 4. Exact control-message and version state machine

After preparation latches at `n_0`, the owner attempts one SNAPSHOT after its
service reservation on ticks `n_0,n_0+2,n_0+4,...`, on the first live tick of a
new `k` epoch, and on any transfer-intent origin tick not already scheduled. It
does so only when both current SOURCE
buffers are nonempty and have the same sequence. Forming a SNAPSHOT activates a
one-tick `lineage_lock` on that exact sequence at the sender. At the next
tick's delivery step, a successfully delivered SNAPSHOT header arms the same
lock at the receiver before SOURCE arrivals are processed. Any newer SOURCE
arrival to a locked UAV is discarded rather than queued, and both buffers
retain the locked packet through snapshot acceptance and any same-hop intent
application. Because every same-hop attempt uses the same addressed physical
margin, a delivered intent from a snapshot/intent origin tick cannot arrive
without that tick's SNAPSHOT header. The lock releases after that application
step. If the SNAPSHOT is lost, the receiver never arms a lock and no same-tick
intent can be delivered. The alternating ordinary cadence leaves the following
tick unlocked so a newer SOURCE can arrive. This is the only SOURCE lock and
creates no extra buffer or instantaneous partner signal.

The opaque SOURCE body is not included. A delivered snapshot is accepted iff

```text
Q_owner.source_sequence
 =Q_standby.source_sequence
 =snapshot.common_SOURCE_sequence,
```

and current owner, service epoch, current pre-reservation
`next_payload_sequence` and `k_epoch` equal its fields. The snapshot's
`post_reservation_next_payload_sequence` is therefore an acceptance-time
version. After acceptance it is historical and is not required to track later
owner SERVICE_RELAY reservations. Otherwise the snapshot is discarded. An
accepted current-epoch snapshot is the only snapshot eligible for assimilation.

After the first accepted snapshot, the standby attempts one READINESS on every
live tick `r` after the service-reservation step. A readiness sent at `r`
prospectively targets the only origin/application pair `(r+1,r+2)`: its
four-state quantities are propagated to boundary `r+2`. Let `m_s[r]` be the
current standby raw motion mean and let `m_o[n_s]` be the owner raw mean in its
accepted snapshot. STRUCTURED, NEVER and both simple rules set the readiness
candidate mean to `m_s[r]`; FLEX sets it to
`m_s[r]+beta[r]*(m_o[n_s]-m_s[r])`. That final candidate mean is serialized in
READINESS and is the candidate boundary action for `r+2`. The owner keeps the
newest delivered matching readiness, but a renewal at `n` may use it for an
intent only when `readiness_tick=n-1`; a lost immediately preceding readiness
therefore fails closed rather than silently changing the prediction horizon.
Every READINESS record binds the accepted snapshot tick; that snapshot's owner,
service epoch, common SOURCE sequence and `k` epoch; and the READINESS send
tick's own post-reservation `next_payload_sequence`. Acceptance requires its
snapshot tick to equal the standby's current accepted snapshot, current owner/
service epoch/common SOURCE/`k` fields to match the accepted snapshot and
readiness as applicable, and current pre-reservation
`next_payload_sequence` to equal only the readiness's own sequence. It is not
compared with the older accepted snapshot next-sequence field. Warmup `w`
counts consecutive shadow updates since the first accepted current-owner
snapshot; it resets on episode reset, owner/service-epoch change or snapshot
age above five ticks, but not merely on a `k` switch. A
current-epoch snapshot is still required. The standby retains its last two
sent readiness records, including the exact serialized-and-decoded float32
final candidate raw mean and local FLEX `alpha`, so an intent can bind the
record from `n-1` through application at `n+1`; no older record is usable.

At a renewal `n` with such a version-valid readiness record, the standby's
authoritative raw motion mean is the record's stored mean rather than a newly
computed replacement; the ordinary four-component Gaussian draw is made at
`n` and the resulting projected standby command is held. With no matching
record, its current head supplies the ordinary raw mean. The four-component
Gaussian is therefore evaluated at origin `n` with the same candidate mean
that will be held through application; FLEX beta has direct policy-likelihood
authority and introduces no boundary-time draw or decision. The owner raw mean
computed at `n` is included in the origin-tick SNAPSHOT for later readiness
records. The intent binds
`readiness_tick=n-1`, and `application_tick` is defined rather than serialized:
it is exactly `origin_tick+1`.

At an ordinary renewal, the current owner combines its owner-head outputs with
the newest delivered readiness/standby commit probability and evaluates the
origin certificate before service reservation. If the arm's effective commit
bit and that certificate are true, then after service reservation it serializes
one `32-byte` transfer intent with the new post-reservation sequence/version and sets
`origin_certificate_pass=true`. It also sends the tick's fresh snapshot under
the same lineage lock; that snapshot includes the owner raw boundary-action
mean used by a possible FLEX blend. IMMEDIATE/HYSTERESIS replace the commit bit
by their rule. Under the same non-commit eligibility mask, NEVER samples/uses
its learned commit bit; a true bit sends one equal-size NOOP with
`request_transfer=false`. This behaviorally live bit changes message
bytes/energy but a NOOP cannot enter the CAS or invalid-commit count. A
delivered transfer intent is handled only at the next tick's application step.
The current owner after that
step sends one COMMIT_RESULT with the first-false reason code. No hidden
acknowledgement or retry exists.

A failed application leaves `handover_used=0` and the preparation latch set;
at a later ordinary renewal STRUCTURED/FLEX/NEVER may make a new stochastic
protocol decision and a simple rule makes another deterministic request when
the current certificate is eligible. This is a new tick/versioned decision,
not retransmission of a lost message. A successful application changes the
preparation state to completed: after its one COMMIT_RESULT, SNAPSHOT,
READINESS and intent/NOOP emissions cease for that trajectory, while STATE,
motion, payload and recurrent updates continue. Thus the limit is one
successful transfer, not one possibly invalid request.

## 5. Prediction, origin certificate and application validation

Each active prediction head emits a current-tick four-dimensional
constant-velocity target-state mean `m_x=(x,y,v_x,v_y)` and ten raw
lower-triangle values. The diagonal
values are `softplus(raw)+1e-3`; off-diagonals are raw. With the resulting
`4x4` lower-triangular `L`,

`P_x=L L^T+1e-4 I_4`.

Use the exact `F,Q,H` from the camera-filter recurrence. For an owner snapshot
emitted at `n_s`, a readiness emitted at `r` and its prospective application
boundary `r+2`, let `d_o=r+2-n_s`:

```text
m_owner(r+2)=F^d_o m_x_owner
P_owner(r+2)=F^d_o P_x_owner (F^d_o)^T
             +sum_{q=0}^{d_o-1} F^q Q (F^q)^T.
```

The standby output available at readiness tick `r` is propagated by the same
recurrence with `d_s=2`. When that readiness is used at origin renewal
`n=r+1`, both predictions therefore refer to its application boundary
`n+1=r+2`. Let position means/covariances be `H m` and `H P H^T`, and
`S=H P_owner H^T+H P_standby H^T+1e-6 I_2`. Then

`d_M^2=(H m_owner-H m_standby)^T S^{-1}(H m_owner-H m_standby)`.

The inverse is evaluated by Cholesky solve. A failed factorization or any
nonfinite input makes the predicate false.

The auxiliary head in a readiness emitted at `r` also emits `q_1,...,q_20`
clipped to `[1e-6,1-1e-6]`, causal probabilities of valid service on ticks
`r+2,...,r+21` if the standby became owner at the prospective boundary `r+2`
and held the stored candidate command.
The training manifest fixes its labels and loss. With the registered
Poisson-binomial convention, start `p_0^(0)=1` and recurse

`p_m^(j)=(1-q_j)p_m^(j-1)+q_j p_(m-1)^(j-1)`

with out-of-range terms zero. Define the one-sided 95% predictive lower score

`Q95=(1/20)*max{m in 0,...,20: sum_{ell=m}^{20}p_ell^(20)>=0.95}`.

For physical role `i` at renewal `n`, define the exact pre-projection Gaussian
action, norm-clipped action and applied command:

```text
y_i[n]=3*tanh(m_i[n])+exp(ell_i[n])*xi_i[n]
b_i[n]=clip_norm(y_i[n],3)
a_i[n]=P_n(y_i[n]).
```

Here `xi_i[n]` is the registered two-component Gaussian sample in training and
is exactly zero in deterministic evaluation. No other quantity called raw,
candidate or unprojected has certificate authority. On an intent origin store
`y_i[n]`, `b_i[n]` and `a_i[n]` for both physical roles in the bound local
origin record; these are protocol state, not additional wire fields.

Let `x^-_{n+1}` be the deterministic one-tick host state obtained from current
state/held commands with future innovation `eta=0`. At originating renewal `n`
define:

```text
RENEW  = ordinary renewal at n
UNUSED = handover_used=0
MATCH  = readiness_tick=n-1; owner, service epoch, equal nonempty SOURCE
         sequence and current k epoch match the accepted snapshot and newest
         delivered readiness as applicable; current pre-reservation next
         payload sequence equals only the newest readiness's own sequence and
         is not compared with the accepted snapshot's historical sequence
AGE    = n-snapshot_tick<=5 and n-readiness_tick=1
WARM   = w>=10 primitive ticks
MAHA   = d_M^2<=5.99
PRED   = Q95>=0.60
MAINT  = x^-_{n+1} is nonterminal, preserves one owner and permits the current
         owner to send through tick n
SEP    = predicted boundary separation>=15 m
SLEW   = ||b_i[n]-a_i[n-1]||_2<=1.5 m/s^2 for both physical vehicles.
```

The origin certificate is the conjunction of those ten predicates and the
applicable `G1` or `G5`. It is false on any absent, stale, mismatched, singular
or nonfinite value. The applied command remains the common projected `a_i[n]`
defined above. Evaluation uses only causal state at `n`; neither future noise
nor hidden evaluator labels enter it. Its Boolean is authenticated in the
post-reservation intent.

### 5.4 Application-time predicate

At tick `n+1`, do not re-evaluate RENEW, `G1/G5`, WARM, MAHA or PRED. Apply the
delivered intent iff every predicate below is true, in this first-false order:

1. message integrity/delivery and `request_transfer=true`;
2. `origin_certificate_pass=true`;
3. `handover_used=0`;
4. `application_tick=origin_tick+1`, the locally retained readiness record has
   `readiness_tick=bound_readiness_tick=origin_tick-1`, and the delivered
   origin-tick SNAPSHOT has `snapshot_tick=origin_tick`;
5. current owner equals `old_owner`;
6. current `service_epoch` equals the intent version;
7. current `next_payload_sequence` equals its post-reservation version;
8. both locked SOURCE buffers equal `common_SOURCE_sequence`;
9. current `k_epoch` equals the intent version;
10. `terminal[n_app]=false`;
11. application MAINT: one owner, both buffers present, positive batteries and
    no buffer clear under the proposed CAS;
12. application separation is the conjunction

    ```text
    SEP_current = ||p_0[n_app]-p_1[n_app]||_2>=15 m
    SEP_next    = ||(p_0[n_app]+dt*v_0[n_app])
                    -(p_1[n_app]+dt*v_1[n_app])||_2>=15 m;
    ```

13. `SLEW_application` is
    `||b_i[n_app-1]-a_i[n_app-2]||_2<=1.5 m/s^2` for both stored origin
    actions.

No sampled `y`, applied `a`, raw-head mean or another action convention may be
substituted for the displayed `b` in origin or application SLEW.

Success executes the section-1 CAS/promotion before current observations and
motion are chosen. Failure changes no owner/state/buffer and increments exactly
one invalid commit. In either case the lineage lock then releases. This
application predicate, not the origin certificate, controls invalid-commit
accounting.

## 6. Named arms

- `PHYSICS-CERTIFIED-SHADOW-HANDOVER` (`STRUCTURED`) uses learned prepare and
  commit bits plus the common certificate and the promotion law at `alpha=1`.
- `FLEXIBLE-SHADOW-CONTAIN` (`FLEX`) uses the same law with only the four
  unmasked freedoms in section 7.
- `NEVER-HANDOVER` uses the full graph, dual-state motion, message state
  machine and prediction. Under the same non-commit certificate mask its live
  learned commit bit emits an equal-size NOOP intent when true and pays its
  charge, but every effective compare-and-swap is false. That NOOP is a
  stochastic policy action but cannot enter the CAS or invalid-commit count.
  The initial owner remains the payload owner.
- `IMMEDIATE-ELIGIBLE` ignores the effective learned prepare/commit bits,
  prepares after `G1`, and makes a transfer request at every renewal at which
  its common certificate is true until one succeeds.
- `FIXED-HYSTERESIS` is identical except it prepares after `G5` and transfers
  under the same repeat-until-success rule.

All five arms are separately trained with matched physical tapes, architecture,
updates and optimizer law. Evaluation uses each arm's own checkpoint; no
post-hoc override counts.

## 7. Literal FLEX superset

All arms instantiate the four extra raw heads, but non-FLEX arms mask them to
the constants below. FLEX exposes

```text
DeltaI=0.25*tanh(u_I) in (-0.25,0.25)^128
alpha=1+tanh(u_alpha) in (0,2)
r=0.25*tanh(u_r) in (-0.25,0.25)
beta=tanh(u_beta) in (-1,1).
```

At first snapshot acceptance,

```text
h_shadow_STRUCT=P_h(h_bar)
h_shadow_FLEX=P_h(h_bar+DeltaI[n]).
```

Here `DeltaI[n]` is computed only from pre-assimilation `h_s^S[n-1]` by the
ordered law in section 2.3, never from `h_bar` or the post-update state.

At commit FLEX uses the `alpha` state equation in section 1. Its readiness is
`Q_F=clip(Q95+r,0,1)` and eligibility substitutes `Q_F>=0.60`; its commit logit
is `ell_commit_F=ell_commit+4r`. If `m_o` is the owner raw mean carried by the
accepted snapshot and `m_s` is the standby raw mean at readiness construction,
FLEX constructs

`m_boundary_F=m_s+beta*(m_o-m_s)`

as the final candidate mean sent in READINESS. The matching origin renewal
samples the registered `y` around that mean, forms the authoritative norm-
clipped `b`, then applies `a=P_n(y)`. The resulting applied physical command is
held through application;
the former owner likewise continues its origin command. FLEX uses the bound
readiness record's `alpha` for promotion. It introduces no new boundary RNG or
decision. Subsequent commands use the promoted state normally. Residuals act
before all
common certificate and physical projections; they cannot bypass hard
one-owner, epoch, sequence, terminal, separation or slew predicates.

The STRUCTURED embedding copies every shared weight and sets the four extra
head outputs to `(DeltaI,alpha,r,beta)=(0,1,0,0)`. For an identical causal
history and coupled action draw, first-snapshot states are then equal; the GRU
recurrence preserves equality; readiness, messages and eligibility are equal;
the boundary raw action is equal; common projection preserves it; and the same
compare-and-swap produces equal token, payload-sequence, buffers, promoted
states and future physical actions. Induction over ticks proves componentwise

`FLEX(h;0,1,0,0)=STRUCTURED(h)`

for recurrent states, messages, eligibility, payload state, token state and
physical actions. A later static/emulation check tests conformance but does not
define containment.

## 8. Matched first-trigger REAL/SHAM fork

The primary trigger population is fixed in the inference manifest. Its trigger
time is the application tick `n_app` of a delivered application-valid
STRUCTURED transfer intent. After tick-`n_app` arrivals and buffer replacement
and immediately before its CAS, clone every physical state, all recurrent/
filter states, normalization state, buffers, token/version/lineage-lock state,
held commands and the complete remaining exogenous tape.

- `FORK-REAL` performs the exact STRUCTURED promotion and owner transfer.
- `FORK-SHAM` performs the identical comparisons, messages, latency, byte and
  energy debit and the same observable transaction shell, but it leaves the
  physical owner, active incumbent recurrent state and actuator mapping
  unchanged and performs no promotion.

At the fork transaction both REAL and SHAM increment `service_epoch` exactly
once, preserve `next_payload_sequence` and every UAV/base buffer, set
`handover_used=1`, complete preparation, trigger the identical owner/epoch-
change warmup reset and old-version invalidation, cease subsequent SNAPSHOT,
READINESS and intent/NOOP emissions, and expose identical transaction-complete
bookkeeping to every learned observation. REAL additionally changes owner to
the prepared standby and performs the registered recurrent-state promotion and
actuator remapping. No distinct `transaction_used` state exists; any audit name
for that fact is a literal alias of the matched `handover_used` bit.

Both run exactly ticks `n_app,...,n_app+99`, prohibit a second transfer,
preserve terminal absorption and use the identical future physical tape. REAL
applies the CAS before the remaining operations of `n_app`; SHAM performs the
charged transaction at that same point without authority change. The fork is a
pair of potential outcomes, not a randomized assignment law.

The transaction-tick COMMIT_RESULT is byte-identical in REAL and SHAM and is
attempted by the same nominal promoted physical UAV toward the same former
owner, with the same addressed hop margin and sender energy debit. In SHAM its
success/version fields are counterfactual transaction telemetry only and no
controller or arbiter consumes them; COMMIT_RESULT never edits controller or
token state in either branch. This is the sole fork-specific result-message
override to the ordinary current-owner sender rule.

Because the fork is created only after the intent has passed the complete
application predicate, SHAM's prospective suppression is not an invalid
commit. It increments only `sham_transaction`; every genuine failed
application before a fork retains the ordinary invalid-commit law.

## 9. Deployable information boundary

Policy inputs are exactly the ordered observation and delivered messages in
section 2. There is no base-packet-age acknowledgement. They exclude opaque
SOURCE coordinates, true regime, advantage stratum, target future, future `k`,
future radio/noise, scripted action, counterfactual outcome, remaining episode
time, block/seed/address and hidden ground truth. The centralized critic may
receive identical causal-past privileged state during training only.
