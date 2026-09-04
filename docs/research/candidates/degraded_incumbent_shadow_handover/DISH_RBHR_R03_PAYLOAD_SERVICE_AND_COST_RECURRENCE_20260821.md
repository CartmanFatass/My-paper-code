# DISH RBHR r03 payload, service, terminal and cost recurrence

```text
document_kind=direction_science_payload_service_cost_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-03
host=RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v2
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
stage=definition-only
science_activity_authorized=false
```

This normative recurrence fixes the scored data plane and every cost quantity.
All deliveries have exactly one-tick latency. A failed attempt is lost, is not
queued and is never retried. There is no fragmentation, shared-bandwidth queue
or hidden packet process.

## 1. Tick order

For every live tick `n`, operations occur in this order:

1. deliver attempts made on tick `n-1` whose send-tick physical margin was at
   least `6 dB`;
2. update the UAV camera-only target filters from current camera observations;
3. update source and base buffers by the replacement rules below;
4. compute causal observations, recurrent states, readiness and, at an ordinary
   renewal, held motion commands and any commit proposal;
5. resolve at most one atomic compare-and-swap for boundary `n->n+1`;
6. the owner at tick `n` makes its one service-relay attempt and every scheduled
   control message makes its one attempt;
7. apply motion, energy and terminal recurrences; and
8. score `valid_service[n]` from the base buffer after step 3 and before any
   tick-`n` transmission can arrive.

At `n=0`, all packet buffers are empty, no prior arrivals exist, the owner token
has its generator-assigned physical vehicle, `service_epoch=0`, and the next
owner payload sequence is `0`.

## 2. Responder source packet and controller information fence

At every nonterminal tick the responder broadcasts exactly one `SOURCE`
packet of `40 bytes`:

```text
S_n=(source_sequence=n, source_tick=n,
     z_position[n], z_velocity[n], integrity_tag)
z_position[n]=g_xy(t_n)+epsilon_position[n]
z_velocity[n]=gdot_xy(t_n)+epsilon_velocity[n]
epsilon_position~Normal(0,(2 m)^2 I_2)
epsilon_velocity~Normal(0,(0.25 m/s)^2 I_2).
```

Noise components have distinct `PACKET` addresses. The packet body is opaque
authenticated relay data to both UAV controllers. Integrity succeeds exactly
when margin-threshold delivery succeeds; there is no separate CRC error or
false acceptance. A UAV may observe only the packet's arrival, source sequence,
timestamp and integrity success; it cannot
read `z_position` or `z_velocity`. The base evaluator alone decrypts the body.
Thus the source packet cannot bypass the camera-information mask.

The responder attempts the packet independently to both UAVs over the two
responder-to-UAV radio hops. UAV `i` receives it at tick `n+1` iff its send-tick
margin `M_{g->i}[n]>=6 dB`. This threshold is the complete packet-loss law.
Each UAV has a capacity-one source buffer `Q_i`. A delivered packet replaces
`Q_i` iff its source sequence is larger; equal or older arrivals are discarded.
The buffer is never copied or cleared by handover.

## 3. Camera-only causal target filter

Each controller copy has a four-dimensional camera filter state
`x=(position_x,position_y,velocity_x,velocity_y)` with mean `mu` and covariance
`P`. At reset,

`mu[-1]=(0,0,0,0)` and
`P[-1]=diag(250000,250000,100,100)`.

No true target state, route speed or degradation clock is inserted; the first
and later corrections come only from that physical vehicle's camera
observations.
Let

```text
F=[[1,0,dt,0],[0,1,0,dt],[0,0,1,0],[0,0,0,1]]
Q=diag(0.04,0.04,0.25,0.25)
H=[[1,0,0,0],[0,1,0,0]]
R=4 I_2.
```

Every copy predicts `mu_pred=F mu`, `P_pred=F P F^T+Q`. If its physical vehicle has a
camera observation `z`, it applies

```text
S=H P_pred H^T+R+1e-9 I_2
K=P_pred H^T S^{-1}
mu=mu_pred+K(z-H mu_pred)
P=(I-KH)P_pred(I-KH)^T+K R K^T.
```

If the camera is missing, `mu=mu_pred` and `P=P_pred`. The inverse is the unique
positive-definite inverse after the stated ridge. The encrypted SOURCE body is
never an input. This camera-filter state is a causal controller input. The
snapshot transmits the learned target-prediction mean/covariance defined by the
treatment manifest, not the opaque SOURCE body.

## 4. Owner service relay and base buffer

Only the unique current owner may attempt one `SERVICE_RELAY` per live tick.
If its source buffer is empty it sends no service packet. Otherwise it creates
one `64-byte` packet

```text
R_n=(service_epoch, payload_sequence, relay_tick=n, sender_id,
     complete opaque SOURCE body, source_first_hop_margin).
```

`payload_sequence` is assigned from the token's next-sequence counter and the
counter increments exactly once when this attempt is formed, whether or not it
is delivered. The service packet is attempted on owner-to-base margin
`M_{owner->base}[n]` and arrives on `n+1` iff that margin is at least `6 dB`.
Its stored second-hop margin is the send-tick value.

The base has a capacity-one buffer `B`. Among its previous contents and every
arrival on the tick, it retains the lexicographically largest tuple

`(source_sequence, relay_tick, service_epoch, payload_sequence, -sender_id)`.

The base does not clear its prior packet at a service-epoch change. An arriving
packet is admissible only if its sender held the token and the enclosed epoch
was authoritative on its send tick; an in-flight old-owner packet therefore
remains a valid historical packet but cannot masquerade as a new-owner send.

For a selected base packet at tick `n`, define

```text
age[n]=(n-source_tick(B))*dt
g_hat[n]=z_position(B)+age[n]*z_velocity(B)
position_error[n]=||g_hat[n]-g_xy(t_n)||_2.
```

Absent-buffer values are `age=position_error=+infinity` and both margins
`-infinity`. The literal score is

```text
valid_service[n]
 = 1{terminal[n]=0}
 * 1{B[n] exists}
 * 1{age[n]<=0.5 s}
 * 1{position_error[n]<=8 m}
 * 1{source_first_hop_margin(B[n])>=6 dB}
 * 1{owner_to_base_second_hop_margin(B[n])>=6 dB}.
```

Neither owner flags, arm labels, regime labels, readiness, controller beliefs
nor handover events enter this equation.

## 5. Fixed control-wire sizes and emission counts

Wire sizes include headers and integrity fields:

| message | bytes |
|---|---:|
| `SOURCE` | 40 |
| `SERVICE_RELAY` | 64 |
| `SNAPSHOT` | 96 |
| `READINESS` | 48 |
| `COMMIT_INTENT` or `NOOP_INTENT` | 24 |
| `COMMIT_RESULT` | 24 |

The treatment manifest fixes exactly when each control packet is emitted and
the radio hop it uses. Each named emission is one attempted packet and counts
its bytes whether delivered or lost. All five learned arms execute the same
message-state machine; their causal states may cause different legal emission
counts. There is no uncounted controller communication.

## 6. Energy, battery and terminal state

Before terminal, UAV `i` consumes propulsion power

`P_i[n]=650+1.5||v_i[n]||_2^2+12||a_i[n]||_2^2 W`.

Every transmitted byte by a UAV consumes an additional `0.02 J`; responder
SOURCE energy is external and is not charged to either arm, although SOURCE
bytes are reported. Battery recurrence is

`B_i[n+1]=max(0,B_i[n]-dt*P_i[n]-0.02*tx_bytes_i[n])`.

Let

```text
separation_breach[n]=1{terminal[n-1]=0 and ||p_1[n]-p_2[n]||_2<15 m}
battery_exhaustion[n]=1{terminal[n-1]=0 and min_i B_i[n]<=0}
terminal[-1]=0
terminal[n]=terminal[n-1] OR separation_breach[n] OR battery_exhaustion[n].
```

After terminal, positions freeze, velocities and commands are zero, all packet
and control attempts stop, packet buffers remain unchanged, and service stays
zero. Controller/filter/protocol states hold their terminal values and no new
policy decision is sampled. To prevent a terminal trajectory from gaining an
energy advantage, each UAV continues to accrue exactly `650*dt J` of absorbing
baseline propulsion on every remaining tick and obeys
`B_i[n+1]=max(0,B_i[n]-650*dt)`. Service deficit continues. No later protocol,
slew, battery or separation event is recounted.

## 7. Literal event and cost indicators

On every tick:

```text
protocol_bytes[n] = 40
                    +64*(number of SERVICE_RELAY attempts)
                    +96*(number of SNAPSHOT attempts)
                    +48*(number of READINESS attempts)
                    +24*(number of COMMIT_INTENT or NOOP_INTENT attempts)
                    +24*(number of COMMIT_RESULT attempts)
```

After terminal this value is zero. The SOURCE term is identical across arms
but remains reported.

```text
invalid_commit[n] = number of delivered intents that request a transfer but
                    do not produce their specified compare-and-swap because
                    any common-certificate or authority predicate is false
token_gap[n]       = 1{number of owner bits is 0}
dual_owner[n]      = 1{number of owner bits exceeds 1}
dual_payload[n]    = 1{more than one UAV makes SERVICE_RELAY attempt}
buffer_clear[n]    = 1{a successful commit changes any nonempty Q_i or B to empty}
command_slew_breach[n]
                   = 1{max_i ||a_i[n]-a_i[n-1]||_2>1.5+1e-12}
separation_breach[n]
                   = as defined in section 6.
```

The authoritative one-owner representation should make gap, dual-owner,
dual-payload and buffer-clear counts structurally zero; they are still measured
rather than assumed.

For a tick window `W`, the cost vector is

```text
C(W)=(sum_{n in W,i} propulsion_energy_i[n],
      sum_{n in W} protocol_bytes[n],
      sum invalid_commit, sum token_gap, sum dual_owner, sum dual_payload,
      sum buffer_clear, sum command_slew_breach, sum separation_breach,
      min_{n in W} ||p_1[n]-p_2[n]||_2).
```

Full-arm cost uses all `1,200` episode ticks. REAL/SHAM cost uses its exact
`100` post-trigger ticks. The 20-second event service window and 50-tick
advantage assay do not redefine the cost windows. Protocol bytes and minimum
separation are reported separately; they are not silently scalarized.

## 8. One-owner handover invariants

A successful commit transfers `(owner,service_epoch,next_payload_sequence)` as
one compare-and-swap. Both local SOURCE buffers and the base buffer persist.
The old owner can form its final packet only before the boundary and the new
owner can form its first packet only after it. A matching source sequence in
the certificate proves the new owner has directly received the same responder
lineage; no opaque body is copied through the snapshot. Consequently every
scored post-handover packet still traverses responder-to-new-owner and
new-owner-to-base physical hops.

Any departure from the tick order, buffer capacities, loss rule, message size,
terminal tail or cost window is a science-bearing change, not an implementation
choice.
