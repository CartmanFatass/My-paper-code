# DISH RBHR r04 total RNG allocation table

```text
document_kind=direction_science_total_rng_allocation
direction_id=degraded_incumbent_shadow_handover
object_revision=DISH-RBHR-SCIENCE-20260821-04
host=RIDGE-BEND-HOT-STANDBY-RELAY-2UAV-v3
owner=Portfolio-owned direction EM /root/em_dish_rbhr_refresh
stage=definition-only
science_activity_authorized=false
```

This table completes the address schema in the host manifest. Every stochastic
quantity has exactly one row. Coordinates not assigned by a row are `NONE`.
No implementation-chosen field string or auxiliary RNG is legal.

## 1. Finite field vocabulary

`field` is exactly one of:

```text
ROUTE_SPEED|TURN_MAGNITUDE|TURN_SIGN|INITIAL_UX|INITIAL_UY|PHASE_OFFSET|
OMEGA_PERM_SCORE|ARM_PERM_SCORE|WIND_X|WIND_Y|CAMERA_U0_X|CAMERA_U0_Y|
CAMERA_U1_X|CAMERA_U1_Y|RADIO_EPSILON|SOURCE_POSITION_X|
SOURCE_POSITION_Y|SOURCE_VELOCITY_X|SOURCE_VELOCITY_Y|PARAMETER_UNIFORM|
MOTION_OWNER_X|MOTION_OWNER_Y|MOTION_STANDBY_X|MOTION_STANDBY_Y|
PREPARE_BERNOULLI|COMMIT_BERNOULLI|MINIBATCH_PERM_SCORE|BOOTSTRAP_BLOCK
```

There is no packet-loss field because delivery is the deterministic radio-margin
threshold. Fixed biases, fixed log standard deviations, FLEX-zero heads,
identity choices and scripted tie breaks consume no draw.

## 2. Evaluation candidate and accepted-tape binding

For evaluation split `X in {CLAIM,CALIBRATION}`, each candidate is identified
by `(block,regime,schedule,accepted_slot,candidate_attempt)`. These rows use
`arm_substream=COMMON`, `degradation_flag=PAIR_SHARED`,
`fork_branch=PREFORK`, and no lane/cycle/episode:

Give the requested advantage strata ordinals
`POSITIVE=0, NEAR_ZERO=1, NEGATIVE=2`. For within-stratum slot
`ell=0,...,15`, the address coordinate is exactly
`accepted_slot=16*stratum_ordinal+ell`; thus the ranges `0..15`, `16..31` and
`32..47` are disjoint and no free-text stratum coordinate is needed.

| quantity | purpose | tick | message | sequence | hop | field | draw index |
|---|---|---:|---|---:|---|---|---:|
| route speed | `TARGET` | `NONE` | `NONE` | `NONE` | `NONE` | `ROUTE_SPEED` | 0 |
| turn magnitude | `TARGET` | `NONE` | `NONE` | `NONE` | `NONE` | `TURN_MAGNITUDE` | 0 |
| turn sign | `TARGET` | `NONE` | `NONE` | `NONE` | `NONE` | `TURN_SIGN` | 0 |
| initial `u_x` | `INIT` | `NONE` | `NONE` | `NONE` | `NONE` | `INITIAL_UX` | 0 |
| initial `u_y` | `INIT` | `NONE` | `NONE` | `NONE` | `NONE` | `INITIAL_UY` | 0 |
| wind innovation x/y | `WIND` | `n` | `NONE` | `NONE` | `NONE` | `WIND_X`/`WIND_Y` | 0,1 |
| camera noise by vehicle/component | `CAMERA` | `n` | `NONE` | `NONE` | `NONE` | `CAMERA_U0_X`...`CAMERA_U1_Y` | 0,1 per normal |
| radio margin noise | `RADIO` | `n` | `NONE` | `NONE` | exact physical hop | `RADIO_EPSILON` | 0,1 |
| SOURCE position noise x/y | `PACKET` | `n` | `SOURCE` | `n` | `NONE` | `SOURCE_POSITION_X`/`Y` | 0,1 per normal |
| SOURCE velocity noise x/y | `PACKET` | `n` | `SOURCE` | `n` | `NONE` | `SOURCE_VELOCITY_X`/`Y` | 0,1 per normal |

One SOURCE body is constructed from the four `hop=NONE` values and used
byte-for-byte on both responder-to-UAV attempts. `RADIO_EPSILON` alone uses
`G_TO_U0` or `G_TO_U1` for those hops.

There is exactly one addressed physical margin per directed hop and tick. All
messages attempted on the same directed hop during that tick use that same
margin; message type and packet sequence are therefore `NONE` in every RADIO
address. Distinct directed hops use distinct addresses.

For a requested stratum, let `a*` be the smallest candidate attempt in
`0,...,99999` whose complete scripted assay meets that stratum and all admission
conditions. The accepted tape is exactly the candidate state and every future
physical value at the same full address with `candidate_attempt=a*`. All five
learned arms, its mask-off pair and any REAL/SHAM fork reuse those physical
addresses; no accepted-tape redraw exists. Mask-on/off is a deterministic view.
REAL and SHAM use the same `PREFORK` physical values after cloning. The
`SCRIPT_TRANSFER`, `SCRIPT_RETAIN`, `REAL` and `SHAM` branch tokens identify
deterministic bookkeeping only and never address exogenous noise.

The one cell-level phase offset uses purpose `K_SCHEDULE`, its actual evaluation
split, block/regime/schedule, with accepted slot and candidate attempt `NONE`,
`field=PHASE_OFFSET`, `draw_index=0`; it is mapped to
`floor(k_initial*U)`. Onset, switch, reflection, owner and physical-ID assignment
are deterministic slot functions and consume no draw.

## 3. Training physical tapes and clocks

For training lane episode `(block,regime,schedule,lane,episode_wave)`, use
`split=TRAIN`, `accepted_slot=candidate_attempt=NONE`, `cycle=NONE`,
`arm_substream=COMMON`, `degradation_flag=DEGRADED_ONLY`,
`fork_branch=NONE`, and `episode=episode_wave`. Route, initial geometry, wind,
camera, radio and SOURCE rows are identical to section 2 with those training
coordinates. Thus physical tapes are common across arms but fresh across lane,
episode, schedule, regime and block.

For each training schedule and permutation cycle `c`, each item of its finite
Omega list receives one score at purpose `K_SCHEDULE`, split `TRAIN`,
block/regime/schedule, `cycle=c`, `field=OMEGA_PERM_SCORE`, and
`draw_index=item_ordinal`. Sorting score then ordinal is the permutation.
Lane-episode coordinate `m=4*episode_wave+lane_within_cell` consumes item
`m mod |Omega|` from cycle `floor(m/|Omega|)`. Identity/reflection comes from
the independent deterministic `m mod 8` bit law in the training manifest.

## 4. Arm assignment and learned randomness

Within block `b`, each arm-substream slot ordinal `j=0,...,4` receives one
score with purpose `ARM_PERM`, split `TRAIN`, block `b`,
`field=ARM_PERM_SCORE`, `draw_index=j`. Sorting score then slot ordinal maps the
listed arm labels `(STRUCTURED,FLEX,NEVER,IMMEDIATE,HYSTERESIS)`, in that order,
to the sorted slot sequence once for the block.

Parameter initialization uses purpose `INIT`, split `TRAIN`, block and assigned
arm slot, `cycle=module_ordinal`, `field=PARAMETER_UNIFORM`, and
`draw_index=column_major_element_index`. Module ordinals are exactly:

```text
0 encoder_W1; 1 encoder_W2;
2 GRU_Wz; 3 GRU_Uz; 4 GRU_Wr; 5 GRU_Ur; 6 GRU_Wh; 7 GRU_Uh;
8 motion_W; 9 prepare_W; 10 commit_W;
11 prediction_mean_W; 12 prediction_cholesky_W; 13 service_q_W;
14 link_mean_W; 15 link_sigma_W; 16 missing_W;
17 snapshot_encoder_W; 18 snapshot_bridge_W;
19 flex_DeltaI_W; 20 flex_alpha_W; 21 flex_r_W; 22 flex_beta_W;
23 critic_W1; 24 critic_W2; 25 critic_Wout.
```

Every associated bias is fixed zero; FLEX module weights 19–22 are also fixed
zero at initialization and therefore consume no initial draw. The four global
motion log-standard deviations are fixed `-0.5` and consume no draw.

At a live training renewal, raw Gaussian noise uses purpose `POLICY_SAMPLE`,
split `TRAIN`, full physical lane/episode/tick coordinates and assigned arm
slot. The four fields `MOTION_OWNER_X`, `MOTION_OWNER_Y`,
`MOTION_STANDBY_X`, `MOTION_STANDBY_Y` each use draw indices `0,1` for one
Box-Muller normal. Active prepare and commit Bernoulli decisions use fields
`PREPARE_BERNOULLI` and `COMMIT_BERNOULLI`, draw index zero, with result
`1{U<p}`. A masked/inactive Bernoulli consumes no draw. Evaluation is
deterministic and consumes no policy-sample draw.

For PPO update `u=0,...,1023`, epoch `e=0,...,3` and recurrent-fragment ordinal
`f=0,...,63`, assign a score using purpose `TRAIN_TAPE`, split `TRAIN`, block,
arm slot, `cycle=u`, `episode=e`, `tick=f`,
`field=MINIBATCH_PERM_SCORE`, draw index zero. Sorting score then fragment
ordinal supplies the one epoch permutation; consecutive groups of eight
fragments form the eight minibatches.

AdamW, normalization, advantage arithmetic, passive-label clones and all
scripted policies are deterministic given the addressed data and consume no
additional draw.

## 5. Inference

For bootstrap resample `g=1,...,99999` and position `q=0,...,23`, use purpose
`INFERENCE`, split `BOOTSTRAP`, all physical coordinates `NONE`,
`inference_resample=g`, `tick=q`, `field=BOOTSTRAP_BLOCK`, draw index zero.
Select block `floor(24*U)`. The same 24-index vector is used for every frozen
estimand in that resample.

## 6. Distribution mapping and completeness

The host manifest's SHA-derived uniform and Box-Muller equations control all
rows. Route/geometry categorical variables use equal-width inverse-CDF bins in
the displayed list order. Xavier matrix elements map `U` affinely to their
matrix-specific interval. Permutations sort their scores with ordinal tie
breaks. There is no stochastic packet loss, dropout, evaluation action,
optimizer shuffle outside the named fragment permutation, randomized fork,
random script tie break or hidden implementation RNG.

Any future random requirement not mapped by this table is
`INVALID_PROTOCOL_OR_MEASUREMENT`, not an implementation choice.
