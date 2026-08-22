# DISH ridge-bend hot-standby relay r04 host, generator and RNG manifest

```text
document_kind=direction_science_host_generator_rng_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-04
host=RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
stage=definition-only
science_activity_authorized=false
```

This file is normative. Together with the r04 science card, the total RNG
allocation table and the four other named r04 normative manifests, it is one
indivisible replacement for r03. R03 supplies no default. A
disagreement among those files is `INVALID_PROTOCOL_OR_MEASUREMENT`; no
implementer may resolve it by preference.

## 1. Primitive clock, state and deterministic operators

`dt=0.1 s`. Episode ticks are `n=0,...,1199`; tick time is `t_n=n*dt`.
Every interval in this revision is half open. For a vector `x`,

`clip_norm(x,c)=x*min(1,c/max(||x||_2,1e-12))`, with `clip_norm(0,c)=0`.

World units are metres, seconds, metres/second and metres/second squared.
Ridge-Base is `b=(-600,0,20)`. The two UAVs fly at fixed altitude `90 m`.
At the start of tick `n`, UAV `i` has horizontal position `p_i[n]`, velocity
`v_i[n]`, held command `a_i[n]` and battery `B_i[n]`. Before terminal,

```text
p_i[n+1] = p_i[n] + dt*v_i[n]
v_i[n+1] = clip_norm(v_i[n] + dt*(a_i[n] + w[n]), 18)
w[n+1]   = clip_component(0.95*w[n] + 0.05*eta[n], -1.5, 1.5)
```

`w[0]=(0,0) m/s^2` deterministically. `eta[n]` has independent standard-normal
horizontal components. A motion
command is renewed only at its ordinary external-`k` renewal and is otherwise
zero-order held. Every arm applies the common command operator

```text
P_n(a_raw)=clip_norm(a[n-1]
                    + clip_norm(clip_norm(a_raw,3)-a[n-1],1.5),3).
```

Thus acceleration is at most `3` and the commanded acceleration slew is at
most `1.5 m/s^2` per primitive tick. `a[-1]=(0,0)` for both UAVs.

## 2. Terrain, visibility and radio

The unreflected terrain is

```text
H(x,y)=135*exp(-(x/75)^2-(y/220)^4)
      +55*exp(-((x-90)/35)^2-((y+40)/85)^2).
```

For endpoints `q0,q1`, ray samples are exactly `q(j)=q0+(j/128)(q1-q0)`,
`j=1,...,127`. A camera ray is clear iff every sample height is strictly
greater than terrain plus `5 m` and its three-dimensional range is at most
`500 m`. A clear camera returns target horizontal position plus independent
normal noise with standard deviation `2 m` in each component; otherwise it
returns one missingness bit and no position.

For a radio hop with three-dimensional length `d`, `blocked=1` iff any ray
sample is at or below terrain plus `8 m`, and otherwise `blocked=0`. Its margin
is

`M=30-20*log10(max(d,1)/100)-35*blocked+epsilon`,

where `epsilon~Normal(0,1 dB)` is independently addressed. A transmission is
delivered exactly one primitive tick later iff its send-tick margin is at least
`6 dB`. There is no additional Bernoulli packet loss, retry or queue.

## 3. Ground-responder route

Independently for every base tape,

```text
v_g ~ DiscreteUniform({4,6,8}) m/s
abs_theta ~ DiscreteUniform({25,35,45}) degrees
sign_theta ~ DiscreteUniform({-1,+1})
theta=sign_theta*abs_theta*pi/180.
```

Evaluation `tau_d` is fixed only by the accepted-slot law in section 5;
training `tau_d` is fixed only by the Omega permutation in the training
manifest. No additional onset draw is made. The unreflected responder begins at
`(-v_g*tau_d,-120,0)` and follows

```text
g(t)=(-v_g*tau_d+v_g*t,-120,0),                         t<=tau_d
g(t)=(v_g*(t-tau_d)*cos(theta),
      -120+v_g*(t-tau_d)*sin(theta),0),                 t>tau_d.
```

Responder velocity is left-continuous at the turn:

```text
gdot_xy(t)=(v_g,0),                                     t<=tau_d
gdot_xy(t)=v_g*(cos(theta),sin(theta)),                  t>tau_d.
```

The SOURCE packet and all scripted controllers therefore use `(v_g,0)` exactly
at `tau_d`.

All route, clock, initial-state and stochastic addresses are fixed before an
arm acts. No realized learned action, trigger, service or outcome selects a
tape.

## 4. The two registered degradation packages

The only claim regimes are package names, not guaranteed pure channels.
For both packages the added intervention is active exactly on ticks satisfying

`tau_d <= n*dt < tau_d+4.0 s`.

No added regime intervention is active before `tau_d`.

1. `TARGET-VISUAL-MASK-PACKAGE`: during that interval, the incumbent camera is
   additionally missing when its target ray intersects the closed vertical
   prism `x in [-20,30]`, `y in [-155,-85]`, `z in [0,120]`. It injects no
   additional radio impairment. Ordinary terrain- and noise-induced radio
   failure remains possible, so this is not a pure sensing-only regime.
2. `TERRAIN-RELAY-MASK-PACKAGE`: during that interval, the incumbent-to-base
   radio hop receives one additional `35 dB` blocked penalty when its ray
   intersects the closed prism `x in [-30,45]`, `y in [-80,80]`,
   `z in [0,130]`. It injects no additional camera impairment. Ordinary
   terrain- and range-induced camera missingness remains possible, so this is
   not a pure relay-only regime.

The generator-assigned initial owner is the physical `incumbent` for purposes
of the added mask. The intervention remains attached to that physical vehicle
whether ownership changes before, during or after `tau_d`; it is never moved to
the current owner or the other vehicle. Ordinary pre-onset camera/radio events
may therefore induce a policy handover without redefining the intervention
target.

## 5. Initial state and exact reflection

Let `g0=g(0)`. Independently draw `u_x~DiscreteUniform({-80,-40,40,80})`
and `u_y~DiscreteUniform({-180,-120,120,180})`. Candidate positions are

```text
q_A=(g0_x+u_x,g0_y+u_y,90)
q_B=(g0_x-u_x,g0_y-u_y,90).
```

Both UAVs start at zero horizontal velocity and battery `200,000 J`.
Vehicle names, assignment of `q_A/q_B`, and which vehicle initially owns the
single service token are balanced by the accepted-slot table below.

Reflection has a literal sign `r in {-1,+1}`. For `r=-1`, it transforms the
entire physical world, not only the target: every route, UAV, base, prism and
ray point `(x,y,z)` becomes `(x,-y,z)`; the terrain used by physics is
`H_r(x,y)=H(x,r*y)`; target turn sign and every horizontal wind, camera-noise,
packet-noise and scripted-controller vector have their `y` component multiplied
by `r`; every two-dimensional covariance becomes `J_r P J_r^T` for
`J_r=diag(1,r)`. Learned actions are not post-transformed: they arise from the
already reflected observation. Scalar radio noise, distances, sequence numbers
and clock values are unchanged. For `r=+1` all quantities are unchanged. These
transformations are applied once, before simulation.

For every sixteen-slot evaluation stratum, slot `ell=0,...,15` deterministically
uses the three bits of `ell mod 8` for reflection, initial owner and `q_A/q_B`
assignment. Bit 0 maps zero/one to reflection `+1/-1`; bit 1 maps zero/one to
initial owner UAV0/UAV1; bit 2 maps zero/one to `q_A` assigned to UAV0/UAV1
(and `q_B` to the other). Each of the eight combinations occurs twice. Candidate draws may
change route/noise values but may not change these balancing bits.

For clock balance, give strata listed ordinals `z=0,1,2` and define the
cell-wide slot `j=16*z+ell`. For a fixed schedule,
`tau_d=(42,54,66)[j mod 3]`. For a switched schedule let `q=j mod 12` and use

```text
tau_d=(42,54,66)[q mod 3]
tau_k=(36,48,60,72)[floor(q/3)].
```

This switch-major order is the sole switched-slot assignment: every Cartesian
pair occurs four times and the onset cycle is unchanged. Initial phase is
`(j+phi_offset) mod k_initial`, where
`phi_offset=floor(k_initial*U)` from the exact allocation-table address for the
block/regime/schedule. Thus every initial phase occurs equally often among the
48 tapes for `k_initial in {4,8,12}`; within a 16-tape stratum counts differ by
at most one. Candidate rejection changes no clock or identity coordinate.

## 6. External-`k` schedules

One parameter vector, normalization state and checkpoint per learned arm is
used for every schedule.

- Training schedules are fixed `k=4`, fixed `k=12`, `4->12`, and `12->4`.
- Claim schedules are held-out fixed `k=8`, `4->12`, and `12->4`.
- No-degradation calibration schedules are fixed `k=4` and fixed `k=12`.
- For a switch, `tau_k` is in `{36,48,60,72} s`, independently crossed with
  each `tau_d`. Initial renewal phase is in `{0,...,k_initial-1}`.
- A command already in progress finishes. Target filters, recurrent states,
  payload buffers and ownership persist across a switch, while every old-`k`
  readiness certificate expires.

The renewal recurrence is literal. Let `c[0]=phi`, where `phi` is the registered
initial phase, and let `k_active[0]=k_initial`, `k_epoch[0]=0`, `pending[0]=0`,
`switch_seen[0]=0`.

```text
For n>0, carry k_active[n]=k_active[n-1], k_epoch[n]=k_epoch[n-1],
pending[n]=pending[n-1] and switch_seen[n]=switch_seen[n-1] before applying
the rules below.

Before RENEW[n] is evaluated, a switched schedule with switch_seen=0 sets
pending=1 and switch_seen=1 at the first tick n with t_n>=tau_k. It does not
change c[n] or the held command.

RENEW[n]=1 iff c[n]=0.

If RENEW[n]=0:
    hold the previous command;
    c[n+1]=c[n]-1.

If RENEW[n]=1:
    if pending=1, set k_active[n]=k_new, increment k_epoch once, clear pending,
    and invalidate every old-epoch certificate before constructing observation;
    the policy observes the resulting k_active and k_epoch and selects the
    command held beginning on tick n;
    c[n+1]=k_active[n]-1.
```

In either branch, values not explicitly changed carry to tick `n+1`.

For a fixed schedule `pending` is always zero. Before the first renewal, the
reset command `a[-1]=(0,0)` is held. `c[n]` is the observed number of primitive
ticks until the next ordinary renewal.

The policy observes current `k`, the `k` epoch and ticks until the next
ordinary renewal. It never observes future `k`, `tau_d`, `tau_k`, regime,
advantage stratum, candidate attempt, reflection or RNG identity.

## 7. Arm-independent standby-advantage script

Advantage assignment uses no learned parameter, learned state, learned
message, learned certificate or future noise. From reset, both script branches
use the same causal current ground-truth responder position and current vehicle
state. This evaluator-only current state is never supplied to learned arms.

At every ordinary renewal the scripted desired points are

```text
d_owner[n]   = g_xy(t_n) + (-40,0)
d_standby[n] = 0.5*(g_xy(t_n)+b_xy) + (0,60*r).
```

Each vehicle applies

`a_script=P_n(0.08*(d_role[n]-p[n])-0.60*v[n])`.

The token begins at the designated initial owner. A candidate transfer-origin
time is the first ordinary renewal `n` with `tau_d<=t_{n+1}<tau_d+15 s` for which all are
true: exactly one owner exists; the service epoch matches; the standby is at
most `350 m` from the responder and `500 m` from the base; both batteries
exceed `1,000 J`; the deterministic one-tick propagation under the scripted
commands has separation at least `15 m`; both nonempty SOURCE buffers have the
same lineage; and the next-tick application would preserve post-reservation
payload sequence and the nonempty base buffer. If no such renewal exists, the
candidate is ineligible for all three strata and the next candidate attempt is
examined.

The scripted transfer request is formed after the origin tick's service
reservation and applies at tick `n_app=n+1` under the exact r04 tick/version
recurrence. After `n_app` arrivals/buffer replacement and before CAS, make two
copies of complete state/future tape. `SCRIPTED-TRANSFER` changes one owner,
increments epoch, preserves post-reservation next sequence and every buffer;
`SCRIPTED-RETAIN` does not. Both continue the same role-indexed script for
exactly ticks `n_app,...,n_app+49`, with roles updated only in the transfer
branch. Let `A` be transfer minus retain valid-service fraction over those
ticks:

```text
POSITIVE:  A>= 0.10
NEAR-ZERO: |A|<=0.02
NEGATIVE:  A<=-0.10.
```

Intermediate candidates are rejected. For each block, regime, claim schedule,
stratum and accepted slot, attempts are scanned in increasing integer order;
the first eligible candidate in the requested stratum is accepted. At most
`100,000` attempts are legal. Exhausting that cap is a generator failure and
enters `INVALID_PROTOCOL_OR_MEASUREMENT`; the slot is never replaced by a
different law.

## 8. Evaluation and paired no-degradation populations

For each of `24` replicate blocks and every regime x evaluation-schedule cell,
where the schedules are fixed `k in {4,8,12}`, `4->12` and `12->4`, there are
exactly `16` accepted tapes in each of POSITIVE, NEAR-ZERO and NEGATIVE, or
`48` degraded tapes. Fixed `k=4,12` are calibration-only; the other three are
claim schedules. The same accepted physical tape is evaluated under every arm.
Every accepted degraded tape has one paired no-degradation copy that retains
target, wind, camera noise, radio noise, packet noise, initial state,
reflection and complete `k` schedule and disables only the added package
mask/penalty in section 4. Mask-off views are paired copies, not additional
accepted slots. Calibration tapes are fresh and never reused as claim tapes.

The exact competence windows and reducers are defined in the population and
inference manifests. No accepted or calibration tape is removed for terminal,
nontrigger, nonrecapture, support, competence, opportunity, headroom or result.

## 9. Fully addressed RNG

The future activity owner samples one fresh master uniformly from `{0,1}^256`
only after explicit activity authorization. It is not created by this
revision. Every
scalar random draw is addressed by the UTF-8 string

```text
DISH/RBHR/R04/<purpose>/<block>/<split>/<regime>/<schedule>/
<accepted_slot>/<candidate_attempt>/<lane>/<cycle>/<arm_substream>/
<degradation_flag>/<fork_branch>/<episode>/<tick>/<message_type>/
<packet_sequence>/<hop>/<inference_resample>/<field>/<draw_index>
```

Domains are literal:

```text
purpose = INIT|TARGET|WIND|CAMERA|RADIO|PACKET|K_SCHEDULE|TRAIN_TAPE|
          EVAL_TAPE|STRATUM|ARM_PERM|POLICY_SAMPLE|FORK|INFERENCE
block = 0,...,23 or NONE
split = TRAIN|CLAIM|CALIBRATION|FORK|BOOTSTRAP
regime = TARGET_VISUAL_MASK|TERRAIN_RELAY_MASK|NONE
schedule = K4|K8|K12|K4_TO_K12|K12_TO_K4|NONE
accepted_slot = 0,...,47 or NONE
candidate_attempt = 0,...,99999 or NONE
lane = 0,...,31 or NONE
cycle = nonnegative base-10 integer or NONE
arm_substream = COMMON|SLOT0|SLOT1|SLOT2|SLOT3|SLOT4|NONE
degradation_flag = PAIR_SHARED|DEGRADED_ONLY|NO_DEGRADATION_ONLY|NONE
fork_branch = PREFORK|REAL|SHAM|SCRIPT_TRANSFER|SCRIPT_RETAIN|NONE
message_type = SOURCE|SERVICE_RELAY|STATE|SNAPSHOT|READINESS|COMMIT_INTENT|
               NOOP_INTENT|COMMIT_RESULT|NONE
packet_sequence = nonnegative base-10 integer or NONE
hop = G_TO_U0|G_TO_U1|U0_TO_BASE|U1_TO_BASE|U0_TO_U1|U1_TO_U0|NONE
inference_resample = 1,...,99999 or NONE
episode,tick,draw_index = nonnegative base-10 integers or NONE.
```

`field` is not free text. Its complete finite vocabulary and the canonical
full tuple for every draw and permutation are fixed in
`DISH_RBHR_R04_TOTAL_RNG_ALLOCATION_TABLE_20260821.md`; that table also binds an
accepted evaluation tape to its exact winning candidate attempt. Any random
quantity without a row is forbidden.

The five learned labels are assigned within each block to `SLOT0,...,SLOT4`
by sorting their independently addressed `ARM_PERM` uniforms; ties use slot
number. Physical exogenous draws use `COMMON`. Paired degraded/no-degradation
trajectories use `PAIR_SHARED`, so their stochastic values are byte-identical;
the deterministic intervention flag alone differs. REAL and SHAM use
`PREFORK` through the clone and the named branch thereafter. They read the same
future physical values by using `PREFORK` physical addresses; branch-specific
addresses exist only for branch bookkeeping and must not introduce noise.

For an address `a`, let `d=SHA256(master_bytes || 0x00 || UTF8(a))`.
An independent uniform is

`U=((big_endian_integer(d[0:8])>>11)+0.5)/2^53`.

Discrete draws use inverse-CDF bins in the listed order. A standard normal uses
two independently addressed uniforms and
`sqrt(-2 log U1)*cos(2*pi*U2)`. Every vector component and repeated draw has a
distinct `field/draw_index`. Every referenced counter-keyed permutation sorts
the finite listed items by one independently addressed uniform per item and
breaks an exact tie by the item's listed ordinal. Candidate attempts and
accepted slots are scanned in the literal numeric order above; parallel
completion order has no effect.

The allocation table controls all bootstrap, training-lane, permutation,
parameter, policy, packet and rejection coordinates. In particular, one SOURCE
body uses `hop=NONE` and is byte-identical on its two broadcast delivery
attempts; only RADIO margin draws are hop-specific. No training, evaluation,
packet, arm, degradation, fork or inference address is reused for another role
except the explicitly declared `COMMON`, `PAIR_SHARED` and `PREFORK` coupling.

## 10. Forbidden changes

No later actor may tune or replace the host equations, masks, onset/switch
sets, script, stratum thresholds, candidate cap, evaluation counts, pairing,
reflection, address schema, distribution or deterministic enumeration based on
competence, support, headroom, runtime or results. Any such change is a new
science revision requiring same-conversation Pro reclosure before activity.
