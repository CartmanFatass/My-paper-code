# MGTAP B01 native ground-geometry intake — 2026-09-08

## Authority and exact delivery

- Direction/node: `metric_ground_transport_allocation` /
  `em:metric_ground_transport_allocation:convergence`
- Transport request: `2026-09-08-mgtap-native-geometry-reentry-01`
- Fixed scientific source revision: `d726acf63f8db47bd2e93e43cac8bbd27529d8ad`
- Task revision: `5264e5b051d6f36a108dd237ac76e94c0f20fe11`
- Delivery branch and commit: `codex/mgtap` /
  `12a3764e8dded6c1927e67e7beeddb2ff8b573f0`
- Decision authority: `PRO_FINAL`; decision formed: yes
- Final direction decision: `CONTINUE_B_NATIVE_GROUND_GEOMETRY`

The complete response is retained at
`pro_packets/20260908_native_geometry_reentry/archive/RESPONSE.md`. Its
canonical SHA-256 is
`13945ba119f391e2e099785529ab8fed63ca8d811a4861e35e97323ceadd08db`; it has
242 logical lines. The matching GitHub delivery is issue #5 comment
`5596561607`. The short Transport receipt SHA-256 is
`f91086d7c8b70ce2ddc516ff1a9f8f758378d577098e9508aa2f2bc15edf214b`; it is a
link-only receipt and is not substituted for the complete response. Transport
facts are retained in the immutable external archive
`C:/Projects/HMASD/temp/sessions/hmasd-chatgpt-pro-transport/archive/metric_ground_transport_allocation/2026-09-08-mgtap-native-geometry-reentry-01`.

The response reports all fourteen listed scientific paths read at the fixed
source revision and no listed-file access gap. The issue body and matching
delivery comment were rechecked around 22:50 PDT on September 8, 2026;
mutable discussion timing is delivery evidence, not scientific evidence.

## Formed decision and interpretation

The preceding native consultation parked the old balanced-allocation-coordinate
family because a base-distance feature, rank map, nearest-user assignment or
additive service surrogate did not define a source-compatible native
treatment/comparator. This response accepts the concrete re-entry condition:
one geometry-bound actor operation against an equally informed generic actor,
with the native information, velocity action, reward, fixed five-UAV host,
channel/association law, recurrent history and B02 credit convention intact.

The selected object is one typed relation-residual actor (`REL`) versus one
parameter-matched dense residual actor (`DENSE`). The hypothesis is that
sharing nonlinear responses across current records of the same type may use
finite training exposure more effectively. It remains a package-level
performance hypothesis: the source does not establish a positive effect,
generic competence, stable superiority, pure metric causality or deployment
value.

## Source-grounded native boundary

The host has five UAVs, fifty ground users, a 1000 m square, altitude limits
50--150 m, 256 one-second steps, component velocity scale 30 m/s and the
existing free-space/vectorized channel and default reward. Native motion
changes distance-dependent path loss, interference, SINR eligibility and
capacity-limited descending-SINR greedy association. The actual association
law allows at most one UAV per user and up to ten users per UAV. Each actor
owns a legal three-coordinate velocity and recurrent history; it does not own
a persistent rank or choose the connection matrix.

The actor receives the existing 108-dimensional input: own normalized
position, twenty current user rows of relative offsets and normalized SINR,
ten current other-UAV rows of relative offsets and normalized SINR, time and
last velocity/hold fields. Rows are source-ranked, truncated and zero-padded.
The separate global critic remains unchanged. `local_indices`, full global
diagnostics, connection/SINR arrays and base metadata are not added. Therefore
the supported route is:

```text
reset geometry and joint motion -> current local records and actor history
-> legal velocity density -> native motion/interference/association
-> primitive team reward -> common PPO advantage -> later service
```

The learner must sum the original per-agent reward entries for native team
return. An adapter-only averaged scalar is not a substitute.

## Frozen B01 card

The companion card is
`MGTAP_NATIVE_GROUND_GEOMETRY_B01_SCIENCE_CARD_20260908.md`. It freezes the
following complete comparison specification while selecting no code or run:

```text
REL: cU=(1/20) sum_j tanh(U u_j), U=20x3
     cV=(1/10) sum_k tanh(V v_k), V=21x4
     z=tanh(Wx+b+P[cU;cV]), W=64x108, P=64x41
DENSE: z=tanh(W'x+b'+Q tanh(Dx+d)), D=16x108, d=16, Q=64x16
```

Both retain the full 108-to-64 raw affine path and unchanged GRU(64,64),
velocity head, log standard deviations and critic. Row maps and the REL fusion
projection have no biases; fixed denominators 20 and 10 process padded rows.
The DENSE branch sees every raw component. The additional branch subtotal is
2,768 parameters in each arm; each complete proposed learner has 69,079
parameters. This is count matching, not equal computation or hypothesis
classes. Initialize the common parts identically, set `P` and `Q` to zero,
and initialize `U,V,D` privately with fan-in-scaled zero-mean weights and
`d=0`, keeping all parameters trainable.

Both arms use primitive G, no duration or renewal, B02 `agent_compound` PPO,
entropy 0.01, gamma one, no GAE/bootstrap, 32-step recurrent chunks, four
epochs per two-episode 512-step rollout, Adam 3e-4 with betas 0.9/0.999,
epsilon 1e-8, value coefficient 0.5, no weight decay/scheduler and global
gradient clipping 0.5. Agent velocity-coordinate log densities are summed
before the [0.8,1.2] ratio clip; no per-coordinate clip or extra division by
five is added.

Use fresh paired masters 8201 and 8202, one REL and one DENSE fit per master.
Each fit has 512 training episodes (131,072 team steps), 1,024 Adam calls and
32 final sampled evaluation episodes (8,192 team steps). The shared fixed-zero
velocity H reference has 32 evaluation episodes per master. Expected totals
are 2,240 complete episodes, 192 final evaluation episodes and 573,440 team
steps. These are prospective counts, not an execution record.

For sampled episode `J=(1/256) sum_t sum_i r_i,t`. For each master average 32
paired `J_REL-J_DENSE` differences; average the two master differences for
`Delta`. The absolute MEI is 0.01 in complete time-average native team reward.
`Delta > 0.01` is preliminary REL-package advantage; `-0.01 <= Delta <= 0.01`
is no gain at the declared scale but not equivalence; `Delta < -0.01` is
adverse evidence for REL versus DENSE here. Per-master signs and all episode
values remain reportable. H is diagnostic, not a second primary comparator.

DM prediction: the aggregate will be small or inside the MEI. Generic typed
sharing/regularization, rank dilution, and a harmful locally attractive
response under coupled interference remain live alternatives. The prediction
slot is not taken under unattended operation.

## Work, cost and acceptance boundary

The source-derived per-arm cost law is
`C_a=C_init,a+131072*c_env+actor,a+1024*c_update,a+8192*c_eval,a+C_publication,a`.
REL has more arithmetic than DENSE despite the equal branch subtotal (4,664
versus 2,752 matrix-weight products per actor row and 610 versus 16 inner
tanh outputs). Incremental elapsed time, activation memory, RSS and cost
coefficients remain unmeasured; no cost probe, warm-up or fresh calibration was
selected. Before any later sweep, the runner must make its own per-arm cost
projection and refuse an arm exceeding the applicable cap without changing
the card's dtype, device, RNG, comparator or budget.

An eventual CM handoff should implement only the two stated encoders and add
focused checks for fixed-count typed pooling, zero padding, equal 2,768 branch
subtotals, equal zero-projection initial policies, and branch connection to
the velocity loss after the projection moves. Preserve native reward,
information, action density, common PPO credit and recurrent history. A small
forward/backward check and one toy publication check are sufficient. No
stationarity, all-positive-seed, global-diagnostic, binding-ablation or UAV
gate is added.

This intake itself performed zero model construction, scientific imports,
tests, training, evaluation, simulation, result-bearing cost work or compute
exposure. It selects no implementation task, invocation, compute allocation,
UAV-validation entry, retry, resume or Portfolio action. Root must provide a
bounded CM command at a later clean boundary before any implementation or
resource preflight; any result-bearing invocation requires committed and
pushed exact bytes, the configured remote-first route and detached execution.

## Direction, Portfolio and owner effects

Direction effect: freeze this one native geometry B question and keep the old
allocation-coordinate family reversibly parked. No recast count changes and
historical B02/B03 and C meanings remain intact.

Portfolio effect: **none**. Lifecycle, priority, investment, fusion,
registration, working-set membership and UAV-validation state are unchanged.

The Chinese brief is
`docs/research/portfolio/owner/briefs/metric_ground_transport_allocation/2026-09-08_native_ground_geometry_b01.md`.
The direction decision, new-card and brief owner items are generated through
`tools/owner_console/item.py`; they expose reversible options without waiting
for a reply. The decision packet and card packet are companion JSON files in
this direction directory.

Shared Portfolio and audit files are Root-owned. The rows below are
append-ready anchors for `docs/research/portfolio/audit/2026-09-08.md`.

| time | direction | tier | kind | options | chosen option | reversible | provenance label | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-08T22:58:00-07:00 | metric_ground_transport_allocation | direction | selection | (a) continue B01 card; (b) keep native geometry parked; (c) recast native task | (a) `CONTINUE_B_NATIVE_GROUND_GEOMETRY`; no run or Portfolio action | yes | `PRO_FINAL` | `docs/research/portfolio/owner/inbox/2026-09-08/20260908-mgtap-003.json` | none | |
| 2026-09-08T22:58:01-07:00 | metric_ground_transport_allocation | direction | selection | accept; reject; revise | accept B01 card for later bounded CM handoff | yes | `DM_INTAKE / PRO_FINAL` | `docs/research/portfolio/owner/inbox/2026-09-08/20260908-mgtap-004.json` | none | |
| 2026-09-08T22:58:02-07:00 | metric_ground_transport_allocation | object | technical | reading-agreed; reading-disputed | B01 brief recorded; no empirical result or Portfolio action | yes | `DM_INTAKE / PRO_FINAL_REPORTED` | `docs/research/portfolio/owner/inbox/2026-09-08/20260908-mgtap-005.json` | none | |

No owner review instruction was pending at this clean boundary (`item.py
reviews --json` returned `[]`). Existing MGTAP owner items remain historical/open
unless the owner replies through the console; this intake invents no reply.

## Evidence references

- Complete response: `pro_packets/20260908_native_geometry_reentry/archive/RESPONSE.md`
- Frozen card: `MGTAP_NATIVE_GROUND_GEOMETRY_B01_SCIENCE_CARD_20260908.md`
- Prior native boundary: `MGTAP_NATIVE_GEOMETRY_CONVERGENCE_INTAKE_20260908.md`
- Direction authority: `DIRECTION.md`
- Delivery comment: `https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5596561607`
- Accepted source pin: `d726acf63f8db47bd2e93e43cac8bbd27529d8ad`
