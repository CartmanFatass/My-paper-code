# MGTAP B01 — typed native ground-geometry actor comparison

Date: 2026-09-08. Direction: `metric_ground_transport_allocation`; route N5.
Class: **B/EXPLORE**. Object: `mgtap_native_ground_geometry_b01`.
Status: frozen by the DM after the complete same-node `PRO_FINAL`; no model,
implementation, result-bearing invocation, cost probe or UAV-validation entry
is selected by this card.

## Claim, question and ceiling

Claim: on the fixed native five-UAV task, a typed nonlinear relation-sharing
branch may change finite-budget native return relative to an equally informed,
parameter-matched unstructured dense residual branch. This is a package-level
performance question about a learned processing bias. It is not a claim of
metric-specific causality, optimal transport, stable superiority, equivalence,
ground-base value, fleet transfer, churn, warehouse/UAV efficacy, convergence,
safety or general MARL performance.

The question is whether `REL` improves complete sampled native return over
`DENSE` under the same input, recurrent consumer, action, reward, optimizer
convention and declared branch parameter budget. Both arms retain the full
ordered raw actor input, so the treatment receives no information advantage.
The primary observation is native sampled return, not a distance score, rank
change, displacement count or local diagnostic.

The stopped balanced-allocation-coordinate family remains reversibly parked.
This card is the concrete native-actor re-entry supplied by the Pro response;
it does not reopen that old family or either historical C object.

## Native binding and information boundary

The host has five UAVs and fifty ground users in a 1000 m square, altitude
limits 50--150 m, 256 one-second steps and component velocity scale 30 m/s.
The existing free-space/vectorized channel, interference, SINR eligibility,
capacity-limited greedy association and default reward are unchanged. The
actual association rule allows at most one UAV per user and up to ten users per
UAV. Each actor owns its UAV's legal three-coordinate velocity and recurrent
history; it does not choose a connection matrix or persistent slot identity.

The actor input is the existing `x ∈ R^108`: own normalized position, time,
last velocity/hold fields, twenty current user rows `u_j ∈ R^3` containing
relative offsets and normalized SINR, and ten current other-UAV rows
`v_k ∈ R^4` containing relative offsets and normalized SINR. Rows are the
source's SINR-eligible, descending-SINR, truncated and zero-padded records.
The actor keeps all rows and all raw ordered components. The separate global
critic is unchanged. `local_indices`, global diagnostics, connection/SINR
arrays and the metadata base coordinate `[500,500,30]` are not added to either
actor. Persistent IDs and a ground-base service consumer are not assumed.

The source-supported path is:

```text
reset geometry and previous joint motion
  -> current typed local records plus own recurrent history
  -> legal tanh-Gaussian velocity distribution
  -> native motion, interference and greedy association
  -> primitive team service reward and common PPO advantage
  -> later learned velocities and service
```

The learner must recover native team return by summing the original per-agent
reward entries. It must not train on an adapter-only averaged scalar.

## Treatment and comparator

Let `x` be the unchanged 108-dimensional actor input, with user rows `u_j`
(`j=1..20`) and other-UAV rows `v_k` (`k=1..10`). Both branches return 64
features to the unchanged `GRU(64,64)`, velocity mean head and three learned
log standard deviations. Both retain a full raw affine path.

The treatment is the typed relation residual:

```text
cU(x) = (1/20) sum_j tanh(U u_j),       U: 20 x 3
cV(x) = (1/10) sum_k tanh(V v_k),       V: 21 x 4
zREL  = tanh(W x + b + P [cU;cV]),       W: 64 x 108, P: 64 x 41
```

The row maps and fusion projection have no biases. Fixed denominators 20 and
10 are used even when rows are padding. A padded zero row contributes zero to
the branch without a mask, ID or diagnostic. The nonlinear row maps occur
before pooling. The raw path keeps rank information and means that the full
actor is not claimed to be permutation-invariant. No attention matrix,
entity memory, nearest-user search, graph solver or trajectory search is used.

The comparator is the same-information dense residual:

```text
zDENSE = tanh(W' x + b' + Q tanh(D x + d))
D: 16 x 108, d: 16, Q: 64 x 16, W': 64 x 108
```

It sees every original component in both its raw and generic branch. It is not
masked, geometry-blind, fixed-hover or action-reduced. Both packages contain
the original dense G actor as the zero-output-projection special case.

| parameter block | REL | DENSE |
| --- | ---: | ---: |
| shared full raw affine path | 6,976 | 6,976 |
| row maps / hidden affine | 144 | 1,744 |
| context projection | 2,624 | 1,024 |
| additional branch subtotal | **2,768** | **2,768** |
| complete encoder subtotal | **9,744** | **9,744** |

The unchanged GRU, velocity head, log standard deviations and critic match.
Each proposed complete learner therefore has 69,079 parameters, versus the
source G learner's 66,311. This is parameter-count equality for the changed
encoder package, not equality of hypothesis classes, computation, optimization
or useful capacity. The extra parameters are output-connected.

Copy the same original raw encoder, GRU, velocity head, log standard
deviations and critic into both arms. Initialize `P` and `Q` to zero so the
initial policies match the same original G policy. Initialize `U`, `V` and
`D` with independent zero-mean fan-in-scaled uniform weights and initialize
`d=0`; use a private initialization stream. All parameters remain trainable.

## Fixed mode, learner and exposure

Both arms use primitive G mode: no duration head, learned opening hold or
renewal. Each actor chooses a fresh legal velocity at every primitive step;
hovering and repeated commands remain legal. Use the B02 per-agent PPO
convention with `agent_compound` ratio grouping, entropy coefficient 0.01,
ordinary critic, gamma one, no GAE or terminal bootstrap, two-episode
512-step rollouts, 32-step recurrent chunks, four full-rollout epochs,
learning rate 3e-4, Adam betas 0.9/0.999, epsilon 1e-8, value coefficient 0.5,
no weight decay or scheduler and global gradient clipping 0.5. Sum each
agent's three velocity log densities before forming its old/new ratio; clip the
agent ratio to [0.8,1.2], multiply by the unchanged scalar team advantage and
average primitive rows. Do not add per-coordinate clipping or an extra division
by five.

Use two fresh paired masters, **8201** and **8202**. Each master has one REL
fit and one DENSE fit. Seed domains follow the accepted host convention:
common initialization `b+11`, private branch initialization `b+12`, training
velocity generator `b+21`, training resets `b+1000+e`, evaluation resets
`b+2000+e` and private evaluation velocity generator `b+3000+e`, with
`b=100000s`. There is no duration draw. Initial parameters and reset inputs
are paired; trajectories, optimizer state and recurrent histories remain
separate. No rate or width sweep, checkpoint selection, retry or replacement
seed is part of this card.

| work unit | per learned fit | two masters, four fits |
| --- | ---: | ---: |
| complete training episodes, 256 steps each | 512 | 2,048 |
| native training team steps | 131,072 | 524,288 |
| two-episode rollouts | 256 | 1,024 |
| Adam calls, four per rollout | 1,024 | 4,096 |
| final sampled learned-policy evaluation episodes | 32 | 128 |
| learned-policy evaluation team steps | 8,192 | 32,768 |

Retain a fixed-zero-velocity H reference on the same 32 evaluation resets per
master: 64 additional episodes and 16,384 team steps, with no learning or
tuning. H is diagnostic only. Expected total work is 2,240 complete episodes,
192 final evaluation episodes and 573,440 native team steps. These are planned
exposure counts, not evidence of execution.

## Estimand, prediction and result rule

For a complete sampled episode:

```text
J[a,s,e] = (1/256) sum_t sum_i r[i,t]
Delta[s] = mean_e(J[REL,s,e] - J[DENSE,s,e])
Delta    = mean_s Delta[s], for s in {8201, 8202}
```

Use the source's float/float64 accumulation for reporting and retain every
REL, DENSE and H episode value, both pair means, adverse episodes, training
records and pairwise evaluation differences. The declared absolute MEI is
**0.01** in complete time-average native team reward. It is a prospective
scale, not measured headroom and not the old allocation AUC margin.

| result | bounded reading |
| --- | --- |
| `Delta > 0.01` | preliminary REL-package advantage on this native task and exposure; retain baseline qualifications and consider a bounded follow-up |
| `-0.01 <= Delta <= 0.01` | no gain at the declared scale; not equivalence; inspect retained seed and baseline evidence before any change |
| `Delta < -0.01` | adverse evidence for this REL package versus DENSE here; do not carry the unchanged module forward solely on a favorable local statistic |

Opposite seed effects remain explicit. A DENSE fit below H limits claims about
competent generic control but does not erase a trustworthy REL-minus-DENSE
measurement. Missing or corrupt primary measurements quarantine dependent
performance inference; an engineering failure has no scientific polarity.

DM prediction: the two packages will show a small or inside-MEI aggregate,
because shared nonlinear relation responses may improve finite-exposure use of
current records but generic dense processing may already learn the useful map.
The main alternatives are generic typed sharing/regularization, rank dilution
or a harmful locally attractive response under coupled interference. The owner
prediction slot is not taken under unattended operation.

## Cost, checks and stop boundary

Use the source-derived per-arm law:

```text
C_a = C_init,a + 131072*c_env+actor,a + 1024*c_update,a
      + 8192*c_eval,a + C_publication,a
```

REL performs more branch arithmetic than DENSE despite parameter matching:
4,664 versus 2,752 matrix-weight products per actor row and 610 versus 16
inner tanh outputs, excluding common work. These are arithmetic descriptions,
not measured runtime or memory. Incremental elapsed time, activation memory,
RSS and coefficients are unmeasured. Before any future sweep, record the
runner's own per-arm cost projection and refuse any arm whose projection
exceeds the applicable machine-time cap; do not create a result by silently
changing the cap, dtype, device, RNG, comparator or budget. No cost probe or
warm-up is selected by this intake.

An eventual CM implementation must preserve the native reward, actor input,
action density, common PPO credit, recurrent history and primary output. Add
focused checks that fixed-count typed pooling handles padding, both branch
parameter subtotals equal 2,768, the zero projections make paired initial
policies equal, and the changed branch is connected to the velocity loss after
the projection moves. A small forward/backward check and one toy end-to-end
publication check are proportionate; no stationarity gate, all-positive-seed
gate, exact support census, global diagnostic or binding ablation is added.

The card defines a B comparison only. The CM objective is to implement the
two encoders and focused checks within the existing direction checkout after
Root supplies a bounded engineering command. Any result-bearing invocation
must use committed and pushed exact bytes, the configured remote-first route,
node-local memory admission and a detached supervisor. This card itself
authorizes none of those effects. There is no automatic launch, retry, resume,
UAV validation or Portfolio action.

## Provenance and authority

The final answer is
`pro_packets/20260908_native_geometry_reentry/archive/RESPONSE.md` at delivery
commit `12a3764e8dded6c1927e67e7beeddb2ff8b573f0`. Its canonical response
SHA-256 is
`13945ba119f391e2e099785529ab8fed63ca8d811a4861e35e97323ceadd08db`; it has
242 logical lines. The task was read at commit
`5264e5b051d6f36a108dd237ac76e94c0f20fe11`; the fixed scientific source pin
was `d726acf63f8db47bd2e93e43cac8bbd27529d8ad`. Transport's short link-only
receipt SHA-256 was
`f91086d7c8b70ce2ddc516ff1a9f8f758378d577098e9508aa2f2bc15edf214b` and is
not substituted for the complete response. The matching issue delivery was
comment `5596561607` on issue #5. The immutable Transport archive is recorded
at `C:/Projects/HMASD/temp/sessions/hmasd-chatgpt-pro-transport/archive/metric_ground_transport_allocation/2026-09-08-mgtap-native-geometry-reentry-01`.

Decision authority is `PRO_FINAL` and the selected direction decision is
`CONTINUE_B_NATIVE_GROUND_GEOMETRY`. Direction effect: freeze this one B
question while keeping the old allocation-coordinate family parked. Portfolio
effect: none; lifecycle, priority, investment, fusion, registration, working
set and UAV-validation state are unchanged. All new scientific exposure in
this intake is zero.

The Chinese owner brief is
`docs/research/portfolio/owner/briefs/metric_ground_transport_allocation/2026-09-08_native_ground_geometry_b01.md`.
Direction and new-card owner items, plus the brief item, are generated through
`tools/owner_console/item.py`. Shared Portfolio and audit files are Root-owned;
the append-ready audit row is retained in the companion intake.
