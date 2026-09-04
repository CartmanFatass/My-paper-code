# DISH RBHR revision 02 host-generator manifest

```text
document_kind=direction_science_host_generator_manifest
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-02
host=RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v1
owner=Portfolio-owned direction EM
science_activity_authorized=false
```

This manifest removes every target-generator choice from a future CM. A CM may
represent these equations with numerically equivalent code, but may not select
another route, terrain, distribution, stratum, threshold or random stream.

## 1. Coordinates and time

- Primitive step `dt=0.1 s`; episode ticks are `t=0,...,1199`.
- World coordinates are metres. Ridge-Base is fixed at `(-600,0,20)`.
- Both UAVs have fixed altitude `z=90`. Their horizontal state follows

  `p[t+1]=p[t]+dt*v[t]`

  `v[t+1]=clip_norm(v[t]+dt*(a[t]+w[t]),18)`

  with action `clip_norm(a,3)`. A command is zero-order held until its ordinary
  `k` renewal. The common wind follows

  `w[t+1]=clip_component(0.95*w[t]+0.05*eta[t],-1.5,1.5)`,

  where each component of `eta` is standard normal from the sealed WIND stream.
- A physical collision/separation breach is any tick with horizontal UAV
  distance below `15 m`.

## 2. Terrain, visibility and radio

The terrain height in metres is

`H(x,y)=135*exp(-(x/75)^2-(y/220)^4)`

`       +55*exp(-((x-90)/35)^2-((y+40)/85)^2)`.

For endpoints `q0,q1`, the registered ray samples exactly `j=1,...,127` at
`q(j)=q0+(j/128)*(q1-q0)`. A camera ray is clear only when every sampled ray
height exceeds `H(q_x,q_y)+5 m`. Camera range must also be at most `500 m`.

When clear, a UAV receives target position plus independent zero-mean normal
noise with `2 m` standard deviation per horizontal component. When blocked it
receives a missingness bit and no target position. No synthetic interpolation
is inserted by the host.

For a radio hop of three-dimensional length `d`, let `blocked=1` if any sampled
ray height is below `H+8 m`, else `0`. Its margin in dB is

`M=30-20*log10(max(d,1)/100)-35*blocked+eps`,

where `eps` is independent normal noise with `1 dB` standard deviation from the
sealed RADIO stream. A hop is service-valid at `M>=6 dB`.

## 3. Ground-responder route and degradation onset

Each tape draws speed `v_g` uniformly from `{4,6,8} m/s`, turn magnitude
uniformly from `{25,35,45}` degrees and turn sign uniformly from `{-1,+1}`.
Degradation onset `tau_d` is uniform on `{42,54,66} s`.

The responder begins at `(-v_g*tau_d,-120,0)` and moves east so it reaches
`(0,-120,0)` exactly at `tau_d`:

- for `t<=tau_d`, `g(t)=(-v_g*tau_d+v_g*t,-120,0)`;
- for `t>tau_d`, `g(t)=(v_g*(t-tau_d)*cos(theta),
  -120+v_g*(t-tau_d)*sin(theta),0)`.

The target route, `tau_d`, turn, wind, sensor noise, radio noise and every `k`
choice are generated before any policy action.

## 4. Regimes

The same terrain and route are used in both regimes.

### `TARGET-VISUAL-OCCLUSION`

From `tau_d-1 s` through `tau_d+3 s`, the incumbent camera additionally has a
mapped-spur mask exactly when its line segment to the target intersects the
vertical prism `x in [-20,30]`, `y in [-155,-85]`, `z in [0,120]`. The shadow
camera uses the ordinary terrain ray only. Radio physics is unchanged.

### `TERRAIN-RELAY-LOS`

Camera physics is ordinary for both UAVs. From `tau_d-1 s` through
`tau_d+3 s`, the incumbent-to-base radio hop additionally receives the same
`35 dB` terrain-block penalty when its ray intersects the vertical prism
`x in [-30,45]`, `y in [-80,80]`, `z in [0,130]`. The shadow radio uses the
ordinary terrain ray only.

The extra masks are deterministic functions of geometry and time, are visible
only through ordinary missingness/margin observations, and never expose a
regime label to a policy.

## 5. Initial state and identity balance

At `t=0`, let `g0` be the responder position. Draw `u_x` uniformly from
`{-80,-40,40,80}` and `u_y` from `{-180,-120,120,180}`. The two UAV candidate
positions are

`q_A=(g0_x+u_x,g0_y+u_y,90)` and

`q_B=(g0_x-u_x,g0_y-u_y,90)`.

Both start at zero horizontal velocity and equal normalized battery `1.0`.
The incumbent label, vehicle name, reflection `y -> -y`, and assignment of
`q_A/q_B` are crossed exactly and balanced within each replicate. Sensor and
radio-noise laws are identical before geometry acts.

## 6. External-k law

Training and evaluation both use fresh tapes from the same sealed schedule law;
only fixed `k=8` is held out from training.

- Fixed schedules are `k=4`, `k=12`, and evaluation-only `k=8`.
- Switched schedules are `4->12` and `12->4`.
- For a switched schedule, switch time `tau_k` is independently uniform on
  `{36,48,60,72} s` and is crossed as the Cartesian product with every
  `tau_d`. It is never computed from `tau_d`.
- Initial renewal phase is independently uniform on `{0,...,k_initial-1}` and
  balanced. Relative `tau_k-tau_d` is analysis metadata only.
- A command already in progress finishes. New `k` applies at the next renewal;
  no state/buffer reset occurs and any old-epoch readiness certificate expires.

## 7. Standby-advantage strata

Before learned-arm activity, every candidate sealed tape is evaluated with a
future-blind scripted pair from the identical state at the first common
certificate-eligible renewal after `tau_d`:

- `FORCED-SAFE-TRANSFER` atomically transfers the owner token and then applies
  the same proportional geometry controller for `5 s`;
- `SCRIPTED-RETAIN` keeps the incumbent owner and applies that same controller.

Neither controller reads future noise, evaluator labels or learned outputs.
Let `A` be forced-transfer minus retain valid-service fraction in the fixed
five-second window.

- `POSITIVE` iff `A>=0.10`;
- `NEAR-ZERO` iff `abs(A)<=0.02`;
- `NEGATIVE` iff `A<=-0.10`.

Intermediate tapes are outside the registered population. The generator uses
prospective rejection sampling from the STRATUM stream until each
regime/schedule/replicate contains exactly 16 tapes in each stratum. The
selection is complete before learned weights, actions or outcomes exist. All 48
accepted tapes remain in the panel. The stratum is evaluator-only.

## 8. Random streams

All draws use a counter-based generator keyed by the UTF-8 tuple

`DISH/RBHR/R02/<purpose>/<replicate>/<regime>/<schedule>/<tape>/<tick>/<field>`.

`purpose` is exactly one of `INIT`, `TARGET`, `WIND`, `CAMERA`, `RADIO`,
`K-SCHEDULE`, `TRAIN`, `EVAL`, `STRATUM`, `ARM`, or `SHAM-FORK`. The master is
future fresh material created only after a later activity authorization. A
purpose key is never reused across training, evaluation, arms or the first-
trigger fork. Numeric seeds, masters and coordinates do not exist at the
definition stage.

## 9. Forbidden generator changes

No CM may tune the height field, route, masks, onset/switch sets, advantage
thresholds, rejection law, noise, initial geometry, service thresholds or RNG
keys for competence, support, headroom, result balance, cost or runtime. A
change to any of them is a new science revision requiring same-direction EM
authorship and Pro closure before activity.

