# FRRIE B01 post-contact parameter-distance clarification intake

## Authority and formed decision

This note reconciles the complete third round of the persistent
`em:finite_resource_relational_inductive_efficiency:innovator` decision node. It resolves only the
post-contact parameter-distance diagnostic in
`FRRIE-B01-PHY-EDGE-MATCHED-CURVES-20260901`.

- `FINAL_INNOVATOR_DECISION=CLARIFY_PARAMETER_DISTANCE`
- `DECISION_FORMED=true`
- `BLOCKER=NONE`
- `STATE_STAGE=POSTPROJECTION`
- `DOMAIN=EVERY_POSTCONTACT_UPDATE`
- `PARAMETER_SCOPE=EXACT_DECOMPOSITION`
- `DISTANCE_OBJECT=EXACT_COMBINATION`
- `MEASUREMENT_ROLE=MANDATORY_DESCRIPTIVE_NON_GATE`

The response confirms the initially named `L-infinity` norm and freezes its previously missing
state, time, scope, numerical, raw-evidence, reducer, availability, and interpretation semantics.
It does not create a new study, treatment, comparator, threshold, result branch, promotion
predicate, validity rule, estimand, or scientific work term.

## Exact state and time domain

For B01 seed `s` and training update `k`, compare the two arms' operative model states after this
exact sequence:

1. complete the 64-episode full-batch loss;
2. execute one backward call;
3. apply the common global gradient-norm clip;
4. execute the Adam parameter and moment update;
5. apply the arm-specific projection to `beta`;
6. capture model parameters before any next model mutation, rollout, or evaluation.

All non-`beta` parameters are therefore post-Adam values. `beta` is post-Adam and postprojection.
Adam moments are not projected and are excluded from this measurement.

`PRE_UPDATE` is not a separate object because it repeats the previous update's postprojection model
apart from the already covered initialization. `POST_ADAM_PREPROJECTION` is also excluded: it is an
ephemeral proposal state, while the existing per-update `beta` records already retain direct
preprojection and postprojection values and byte-changing contact facts.

Let `kappa_s` be the first update where projecting the PHY post-Adam/preprojection `beta` into
`[-0.15,0.15]` changes at least one stored FP32 value. Boundary contact without an FP32 change is
not contact. The raw parameter-distance trace is required for every integer update
`k=kappa_s..512`.

- `k < kappa_s`: `available=false`, `PRE_TIGHT_CONTACT`;
- `kappa_s <= k <= 512`: required and available;
- no contact through 512: `kappa_s=null`, unavailable at every update with
  `NO_TIGHT_CONTACT_BY_512`.

Pre-contact unavailability is neither zero nor a defect. Existing pre-contact full model-byte and
optimizer-state equality checks remain separate authority.

The complete per-seed trace is retained at every post-contact update. Cross-seed display occurs
only at the existing checkpoints `0,32,64,128,256,512`. Update zero is necessarily unavailable.
There is no roster, intervention, episode, slot, or entity coordinate because one model state is
shared by all subsequent evaluation cells; duplicating it under those coordinates would create
false replication.

## Canonical parameter decomposition

The source is the full ordered 35,513-element learned model, decomposed as:

| Scope | Flat indices | Elements |
|---|---:|---:|
| `FULL_35513` | `[0,35513)` | 35,513 |
| `BETA_18` | `[26982,27000)` | 18 |
| `NONBETA_35495` | `[0,26982) union [27000,35513)` | 35,495 |

The `beta` byte range is `[107928,108000)`. Each arm's complete authoritative parameter blob is
`35,513 * 4 = 142,052` bytes.

The tensor sequence is the literal `LAYER_SHAPES` order, with every tensor flattened in C order and
concatenated as little-endian IEEE-754 binary32:

1. `message_encoder.weight_ih [64,22]`
2. `message_encoder.bias_ih [64]`
3. `message_encoder.weight_ho [32,64]`
4. `message_encoder.bias_ho [32]`
5. `gru.weight_input_zrn [192,55]`
6. `gru.weight_hidden_zrn [192,64]`
7. `gru.bias_zrn [192]`
8. `action_head.weight [6,64]`
9. `action_head.bias [6]`
10. `beta [3,3,2]`
11. `critic.input.weight [64,66]`
12. `critic.input.bias [64]`
13. `critic.hidden.weight [64,64]`
14. `critic.hidden.bias [64]`
15. `critic.output.weight [1,64]`
16. `critic.output.bias [1]`

The decomposition is mandatory because a full-model maximum may be attained directly inside the
projected 18-element tensor while concealing whether divergence has propagated into actor,
recurrent, action-head, or critic parameters. This localization remains descriptive and is not a
causal allocation of return.

## Distance and numerical rule

The exact object is:

```text
EXACT_COMBINATION {
  ELEMENTWISE_SIGNED_DIFFERENCE_VECTOR,
  LINF_FULL,
  LINF_BETA,
  LINF_NONBETA
}
```

The elementwise vector is the recomputation substrate. The three `L-infinity` scalars are the
displayed diagnostic. There is no `L1`, `L2`, normalization, ratio, cosine distance, or parameter-
count adjustment.

For each flat coordinate `j`:

1. decode each arm's four source bytes as finite little-endian binary32;
2. promote each source value exactly to binary64;
3. compute `delta_j = fl64_RN-even(f64(x_PHY_j) - f64(x_EDGE_j))`;
4. compute `abs_j = abs(delta_j)`;
5. take the numeric binary64 maximum over the selected index set.

Thus `D_full=max(D_beta,D_nonbeta)`. The authoritative scalar representation is the exact IEEE-754
binary64 bit pattern, not its printed decimal. There is no accumulation. Optional argmax
localization uses the lowest canonical flat index on a tie.

## Raw state and reference contract

One available record is emitted per post-contact `(seed_block, training_update)`:

```text
FRRIE_B01_PARAMETER_DISTANCE_RAW_V1 {
  seed_block,
  training_update,
  first_tight_contact_update,
  available=true,
  state_stage=POSTPROJECTION,
  capture_boundary=AFTER_ADAM_AND_ARM_PROJECTION_BEFORE_NEXT_MODEL_MUTATION,
  parameter_layout {
    schema=FRRIE_LAYER_SHAPES_V1,
    parameter_count=35513,
    parameter_byte_count=142052,
    dtype=IEEE754_BINARY32,
    byte_order=LITTLE_ENDIAN,
    tensor_flattening=C_ORDER,
    tensor_order=LAYER_SHAPES,
    beta_flat_start=26982,
    beta_flat_end_exclusive=27000,
    beta_byte_start=107928,
    beta_byte_end_exclusive=108000
  },
  phy_state_binding,
  edge_state_binding,
  derived {
    linf_full_binary64_bits_u64,
    linf_beta_binary64_bits_u64,
    linf_nonbeta_binary64_bits_u64,
    full_parameter_bytes_equal,
    optional first_argmax_full_flat_index,
    optional first_argmax_beta_flat_index,
    optional first_argmax_nonbeta_flat_index
  }
}
```

Each arm binding is either `INLINE_PARAMETER_BYTES` or `IMMUTABLE_STATE_REF` and must decode to
exactly 142,052 bytes for the same arm, seed, update, and `POSTPROJECTION` stage. Base64 may transport
inline bytes, but decoded bytes are authoritative.

An immutable reference contains at least:

- `container_schema` and `container_path`;
- `seed_block`, `training_update`, and `arm_id`;
- `field=arm_state_bytes`;
- `decoded_parameter_byte_count=142052`;
- `state_stage=POSTPROJECTION`.

At a B01 checkpoint, the arm-specific checkpoint `arm_state_bytes` may be referenced. At a
noncheckpoint update, direct recomputation requires a dedicated write-once diagnostic state blob.
That blob is not a model-selection checkpoint, cannot be used for resume or evaluation, adds no
checkpoint opportunity, and must be captured symmetrically for both arms without changing
environment, optimizer, or evaluation exposure. Serialization/I/O may be reported as runtime
observation but is not a new scientific work estimand or promotion condition.

A digest, scalar-only record, rounded decimal vector, tensor-name summary, or argmax pair is not
sufficient raw evidence. Optimizer moments and Adam step remain separate objects and must not be
concatenated into the parameter source.

## Reducers and displays

For every available `(s,k)`, report:

- `D_full(s,k)`;
- `D_beta(s,k)`;
- `D_nonbeta(s,k)`;
- `full_parameter_bytes_equal(s,k)`.

There is no within-seed temporal reducer: no max/mean over updates, AUC, contact-aligned integral,
first threshold crossing, work-to-distance, final/initial ratio, or beta/nonbeta ratio.

At each existing checkpoint `u`, include only seeds with `kappa_s <= u`. For each of the three
components report individual seed values, seed identities and count, arithmetic mean, median,
minimum, and maximum. The mean uses binary64 `math.fsum` in B01 seed order followed by one division.
An even-count median uses `math.fsum` on the middle two binary64 values and one division by two.
Unavailable seeds are never zero-imputed. If no seed has contacted, report
`NO_POSTCONTACT_SEEDS`. There is no uncertainty interval, hypothesis test, cross-checkpoint pooling,
or result-selected checkpoint.

## Missingness, nonfinite values, and exact zero

`MEASUREMENT_ROLE=MANDATORY_DESCRIPTIVE_NON_GATE`. It is required because the original B01 decision
named post-contact parameter distance among complete projection/optimizer diagnostics. It is not a
gate because parameter-space separation alone is not evidence of native-return value or relational
semantics and this clarification introduces no threshold, branch, promotion predicate, validity
rule, or work term.

If `k >= kappa_s` but a raw blob/reference is absent, unreadable, partial, incorrectly bound, or the
wrong length:

```text
available=false
availability_reason=PARAMETER_DISTANCE_MEASUREMENT_DEFECT
```

If any raw parameter decodes to NaN/infinity, a derived binary64 result is nonfinite, or stored
scalar bits disagree with direct recomputation:

```text
available=false
availability_reason=PARAMETER_DISTANCE_NONFINITE_RECORD
```

Both defects prohibit zero imputation and parameter-distance inference for that scope, but block
only claims about this diagnostic's magnitude. They create no new `B01_INVALID`, result branch,
threshold, promotion consequence, or scientific polarity. If the learned model itself violates an
existing finite-model or checkpoint rule, any run-level consequence comes from that pre-existing
rule rather than this addendum.

`D_full=0` means all decoded postprojection parameter values are numerically equal at that update.
It does not necessarily mean byte equality because `+0.0` and `-0.0` have equal numeric values but
different FP32 bits; `full_parameter_bytes_equal` distinguishes them. Exact zero does not imply
equal Adam state, earlier/later equality, equal histories, equal symmetric action-TV, equal native
return, or universal non-contact. Component zero patterns localize current numeric divergence only.
A full zero at the recorded contact update conflicts with the combination of genuine FP32-changing
PHY projection and retained paired-update equality facts; surface that inconsistency against the
existing conformance evidence without inventing a new result branch.

## Interpretation limit and unchanged terms

The measurement answers only how far the operative postprojection parameter vectors differ in
maximum coordinate magnitude and whether that maximum lies inside or outside the projected tensor.
It is coordinatewise and scale-sensitive, conflates current and accumulated consequences, and does
not establish functional distance, return causation, optimizer-moment contribution, semantic or
relational mechanism, arm preference, or transport beyond the declared host.

The symmetric PHY/EDGE action-TV addendum remains unchanged. The ordered-28 `V_u(N)` remains the
intact PHY policy versus its one-step rotated PHY shadow and is neither replaced nor satisfied by
parameter distance. Every other B01 term remains unchanged: study identity/class, host, endpoint,
treatment/comparator, seeds, populations, 512-update budget, checkpoints, evaluation panels,
learner/optimizer, RNG, EDGE competence, contact, raw control, ordered-28, support, matched work and
tuning, runtime/memory reporting, validity and interpretation branches, thresholds, promotion,
falsifier, claim ceiling, adaptation record, and R01/R02 separation. Portfolio lifecycle is not
changed by this intake.

## Archive and Transport facts

- Request: `frrie-em-innovator-b01-parameter-distance-clarification-20260901-03`
- Binding: `em:finite_resource_relational_inductive_efficiency:innovator`
- Conversation: `6a96a6c9-1070-83e8-bd90-c528e9cdfda4`
- Response:
  `temp/sessions/hmasd-chatgpt-pro-transport/archive/finite_resource_relational_inductive_efficiency/frrie-em-innovator-b01-parameter-distance-clarification-20260901-03/RESPONSE.md`
- Transport facts:
  `temp/sessions/hmasd-chatgpt-pro-transport/archive/finite_resource_relational_inductive_efficiency/frrie-em-innovator-b01-parameter-distance-clarification-20260901-03/TRANSPORT_FACTS.json`
- Response SHA-256: `9ef284757d0667885cc8009d5a0cba621b728692d94a00de4555acbd509faf8a`
- Provider send evidence: one exact send click, exact user node and attachment observed
- Completion: `NATURAL_COMPLETION`, `ARCHIVED`
- Provider: visible `Pro`, underlying `GPT-5.6 Sol`, effort `5/5`
