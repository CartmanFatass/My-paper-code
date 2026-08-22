# DISH RBHR r05 payload, service, terminal and cost recurrence

```text
document_kind=direction_science_payload_service_cost_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-05
host=RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
stage=definition-only
science_activity_authorized=false
```

This normative recurrence fixes the scored data plane and every cost quantity.
All deliveries have exactly one-tick latency. A failed attempt is lost, is not
queued and is never retried. There is no fragmentation, shared-bandwidth queue
or hidden packet process.

## 1. Controlling tick, delivery and application order

At the start of every tick `n`, execute exactly this order:

1. Compute `terminal[n]` from `p[n]`, `B[n]` and `terminal[n-1]`. If true,
   execute only the absorbing recurrence in section 6, set service zero, and
   perform no tick-`n` delivery, policy decision or transmission.
2. If live, deliver every tick-`n-1` packet/control attempt whose send-tick
   physical margin was at least `6 dB`. Within this delivery step, first expose
   delivered SNAPSHOT/intent headers and arm the receiver's matching one-tick
   SOURCE-lineage lock, then process SOURCE arrivals, then SERVICE_RELAY/base,
   STATE, READINESS and COMMIT_RESULT arrivals. Accept or discard each control
   buffer under the controller manifest. This suborder is deterministic and
   changes no one-tick delivery latency.
3. Determine `RENEW[n]` from the host countdown. If a scheduled switch is
   pending at this renewal, change `k_active` and increment `k_epoch` now, before
   intent validation. Then validate/apply at most one delivered transfer intent
   originating at renewal `n-1`. A successful CAS changes owner, role bits,
   service epoch and payload authority for every remaining tick-`n` operation.
   Record one pending COMMIT_RESULT for transmission later this tick.
4. Update each physical vehicle's camera filter from its current camera
   observation; construct role-conditioned observations; update all recurrent
   copies; and, if `RENEW[n]=1`, choose the tick-`n` held motion and stochastic
   protocol decisions.
5. The resulting tick-`n` owner first reserves/forms its SERVICE_RELAY, if its
   SOURCE buffer is nonempty, and increments `next_payload_sequence`. Only
   afterward are every tick-`n` STATE, SNAPSHOT, READINESS, COMMIT_INTENT,
   NOOP_INTENT and COMMIT_RESULT version field serialized from the same
   post-reservation protocol state. Make each scheduled transmission attempt.
6. Score `valid_service[n]` from the base packet delivered by step 2 and the
   start-of-tick target/terminal state. Then apply tick-`n` motion, propulsion,
   byte-energy and battery recurrences to form state `n+1`.

An intent emitted on tick `n` can first change ownership at step 3 of tick
`n+1`. `n=0` has no arrivals or delivered intent.

Any real packet or control transmission attempted on tick `1199` whose nominal
delivery or application would occur after the episode expires at the horizon.
It produces no tick-1200 state, observation, service or post-episode invalid-
commit event.

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

The exact SOURCE wire order is `source_sequence:uint32`,
`source_tick:uint32`, `z_position_x/y:float32`,
`z_velocity_x/y:float32`, `integrity:uint32`, followed by twelve zero padding
bytes. Integers and floats are little-endian. The complete 40 bytes, including
tag and padding, are the one shared opaque body used on both first-hop
delivery evaluations.

Noise components have distinct `PACKET` addresses. The packet body is opaque
authenticated relay data to both UAV controllers. Integrity succeeds exactly
when a delivered packet's deterministic tag equals the first four bytes of
`SHA256(all preceding serialized message bytes)`. Tags are always generated
correctly and the channel has no bit corruption, so margin-threshold delivery
is the only way a valid packet is absent; there is no false acceptance. A UAV
may observe only the packet's arrival, source sequence,
timestamp and integrity success; it cannot
read `z_position` or `z_velocity`. The base evaluator alone decrypts the body.
Thus the source packet cannot bypass the camera-information mask.

The responder attempts the packet independently to both UAVs over the two
responder-to-UAV radio hops. UAV `i` receives it at tick `n+1` iff its send-tick
margin `M_{g->i}[n]>=6 dB`. This threshold is the complete packet-loss law.
The SOURCE is one physical broadcast body with two link-specific delivery
evaluations, so it contributes 40 reported protocol bytes once, not two
serialized copies; responder energy is external.
Each UAV has a capacity-one source buffer `Q_i`. A delivered packet replaces
`Q_i` iff its source sequence is larger, except that a one-tick lineage lock
defined by the controller manifest discards every arriving SOURCE until its
snapshot/intent application step completes. Equal, older or locked arrivals
are discarded and never queued. The buffer is never copied or cleared by
handover.

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

The exact SERVICE_RELAY wire order is `service_epoch:uint16`,
`payload_sequence:uint32`, `relay_tick:uint32`, `sender_id:uint8`, the complete
40-byte SOURCE body, `source_first_hop_margin:float32`, `integrity:uint32`, then
five zero padding bytes. Integers and floats are little-endian. The base stores
the owner-to-base second-hop margin from the physical send record; it is not a
second copy inside the 64-byte relay.

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
| `STATE` | 64 |
| `SNAPSHOT` | 96 |
| `READINESS` | 48 |
| `COMMIT_INTENT` or `NOOP_INTENT` | 32 |
| `COMMIT_RESULT` | 24 |

Every live tick each UAV attempts one STATE packet to the other UAV, so there
are two `64-byte` STATE attempts. The receiving UAV holds only the newest
delivered STATE by sender tick; older/equal arrivals are discarded. SNAPSHOT
and transfer/NOOP intent are owner-to-standby, READINESS is standby-to-owner, and
COMMIT_RESULT is one current-owner-to-other-UAV attempt. The controller manifest
fixes their exact contents and remaining cadence. Each named emission counts
its bytes whether delivered or lost. There is no base acknowledgement,
unlisted controller message, retry or uncounted partner channel.

The evaluator-only advantage script and recovery witness never emit SNAPSHOT,
READINESS, COMMIT_INTENT, NOOP_INTENT or COMMIT_RESULT. Their live trajectories
still attempt and charge the mandatory SOURCE broadcast body, unique-owner
SERVICE_RELAY and both inter-UAV STATE packets under the same tick, margin and
byte recurrences.

## 6. Energy, battery and terminal state

Before terminal, UAV `i` consumes propulsion power

`P_i[n]=650+1.5||v_i[n]||_2^2+12||a_i[n]||_2^2 W`.

The per-tick propulsion-energy reducer is exactly

```text
propulsion_energy_i[n]=dt*P_i[n]  on a live tick
propulsion_energy_i[n]=650*dt      on an absorbing tick.
```

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
protocol_bytes[n] = 40  (one SOURCE broadcast body)
                    +64*(number of SERVICE_RELAY attempts)
                    +64*(number of STATE attempts)
                    +96*(number of SNAPSHOT attempts)
                    +48*(number of READINESS attempts)
                    +32*(number of COMMIT_INTENT or NOOP_INTENT attempts)
                    +24*(number of COMMIT_RESULT attempts)
```

After terminal this value is zero. The SOURCE term is identical across arms
but remains reported.

```text
invalid_commit[n] = number of delivered request_transfer=true intents that do
                    not produce their specified compare-and-swap under the
                    exact application-time validation predicate, excluding the
                    registered application-valid FORK-SHAM suppression, which
                    is counted only by its sham transaction counter
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

A successful application transfers
`(owner,service_epoch,next_payload_sequence,handover_used)` as one
compare-and-swap at tick-start step 3. Both local SOURCE buffers and the base
buffer persist. The old owner formed its final packet on the prior tick; the new
owner forms its first packet later on the application tick. A matching source
sequence proves the new owner directly received the same responder lineage; no
opaque body is copied through the snapshot. Consequently every scored
post-handover packet still traverses responder-to-new-owner and
new-owner-to-base physical hops.

Any departure from the tick order, buffer capacities, loss rule, message size,
terminal tail or cost window is a science-bearing change, not an implementation
choice.
