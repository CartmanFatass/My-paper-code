# CBSC-OMRC-B01 literal binding specification

Status: `PRO_BOUND / IMPLEMENTATION_READY`

This specification binds the serialization, initialization, adapter, RNG, recurrent-PPO,
evaluation-tape, publication, and resource laws of the already selected `CBSC-OMRC-B01` object on
`CBSC-DYNAMIC-CACHE-2R-1C-v1`. It creates no new scientific object and does not change the host
probabilities, native reward ledger, arm identities, B0/B1/B2 budgets, endpoints, stopping rule, or
B/EXPLORE claim ceiling in `DIRECTION.md`.

Authority is the complete `.02` Innovator clarification in persistent conversation
`6a96a6c0-e918-83e8-a0c0-9dc9222dce1c`, response SHA-256
`e96df981f7cdb40a6206f2fddcc989a05783491a1fa422e7b0ca673344a05844`.

## 1. Primitive token

Every token is exactly 17 bytes, then each byte is expanded least-significant bit first to 136
binary channels:

```text
0 event_kind                 9 body_owner
1 subject_receiver          10 body_epoch
2 target_receiver           11 body_addressed_receiver
3 slot                      12 payload_source_receiver
4 carrier                   13 capability_receiver
5 owner_old                 14 opportunity_index
6 owner_new                 15 event_order_position
7 epoch_old                 16 packed_flags
8 epoch_new
```

Packed flags are `old_need, new_need, body_content, body_native_neutral, access_gated,
request_active, request_need, reserved_zero` at bits `0..7`. Bit 7 is always zero.

`ABSENT_BYTE=255`; `NEUTRAL_PAYLOAD_SOURCE=254`. A byte outside the event's byte mask must be 255;
a flag outside its flag mask must be zero. A present field cannot be 255. Byte 12 may equal 254
only for a native-neutral body. For a byte mask, bit `i` selects byte `i` among bytes `0..15`; for a
flag mask, bit `i` selects flag `i`.

| Code | Kind | Byte mask | Flag mask | Present information |
| ---: | --- | ---: | ---: | --- |
| `0x01` | `INIT_OWNER` | `0x8043` | `0x00` | kind, subject, new OWNER, preamble position |
| `0x02` | `INIT_SEMANTIC` | `0x8103` | `0x02` | kind, subject, new epoch, position; new need |
| `0x03` | `INIT_CAPABILITY` | `0xA011` | `0x00` | kind, carrier, permitted receiver, position |
| `0x04` | `INIT_BODY` | `0x9E19` | `0x0C` | kind, slot, carrier, complete body, position; content/neutral |
| `0x10` | `OWNER` | `0xC063` | `0x00` | kind, subject, old/new OWNER, opportunity, position |
| `0x11` | `SEMANTIC` | `0xC183` | `0x03` | kind, subject, old/new epoch, opportunity, position; old/new need |
| `0x12` | `CAPABILITY` | `0xE011` | `0x00` | kind, carrier, new permitted receiver, opportunity, position |
| `0x13` | `BODY` | `0xDE19` | `0x0C` | kind, slot, carrier, complete body, opportunity, position; content/neutral |
| `0x14` | `NOOP_OWNER` | `0xC001` | `0x00` | kind, opportunity, position |
| `0x15` | `NOOP_SEMANTIC` | `0xC001` | `0x00` | kind, opportunity, position |
| `0x16` | `NOOP_CAPABILITY` | `0xC001` | `0x00` | kind, opportunity, position |
| `0x17` | `NOOP_BODY` | `0xC001` | `0x00` | kind, opportunity, position |
| `0x20` | `DECISION` | `0xFE1D` | `0x7C` | kind, target, slot, carrier, complete body, current carrier binding, opportunity, position; body/content/access/request flags |
| `0x21` | `SETTLEMENT` | `0xC001` | `0x00` | kind, opportunity, position |

All other codes are invalid. The eight preamble tokens use `opportunity_index=255` and positions
`0..7`. For opportunity `t in 0..23`, the four permuted event positions are `0..3`, DECISION is 4,
and SETTLEMENT is 5. An unrealized event emits exactly its family NOOP in its assigned position;
all other bytes are 255 and flags zero. Potential draws still have fixed addresses but are not
revealed and have no state effect.

OWNER's old token must equal pre-token state, then state becomes its new token. SEMANTIC's old epoch
and need must equal pre-token state, then both become their new values. CAPABILITY writes the named
carrier binding and may write its existing value. BODY overwrites the named slot, copying OWNER and
epoch from its addressed receiver at emission. DECISION copies the complete selected slot record and
current binding of that record's carrier, but not current OWNER or epoch. SETTLEMENT exposes no
action, reward, validity, success, or refreshed body; reward uses only the RL reward channel.

## 2. Preamble and initial state

For each episode, independently permute integers `16..63` into `P_OWNER` and `P_EPOCH`. Set
`O_0=P_OWNER[0]`, `O_1=P_OWNER[1]`, `E_0=P_EPOCH[0]`, `E_1=P_EPOCH[1]`. Later realized changes
consume indices `2,3,...` in event chronology. Draw `Y_0,Y_1` independently Bernoulli(1/2), and
`X_0,X_1` independently uniform over receivers.

For each slot independently, draw addressed receiver and carrier uniformly, then role
`CORRECT/SWAPPED/NEUTRAL` with probability `0.50/0.25/0.25`. For addressed receiver `a`, body OWNER
and epoch are `O_a,E_a`. CORRECT uses source `a` and content `Y_a`; SWAPPED uses source `1-a` and
content `Y_(1-a)`; NEUTRAL uses source 254, content 0, and neutral flag 1. The carrier need not
initially permit `a`.

The exact no-action preamble is:

| Position | Token |
| ---: | --- |
| 0 | `INIT_OWNER(receiver=0, owner_new=O_0)` |
| 1 | `INIT_OWNER(receiver=1, owner_new=O_1)` |
| 2 | `INIT_SEMANTIC(receiver=0, epoch_new=E_0, new_need=Y_0)` |
| 3 | `INIT_SEMANTIC(receiver=1, epoch_new=E_1, new_need=Y_1)` |
| 4 | `INIT_CAPABILITY(carrier=0, capability_receiver=X_0)` |
| 5 | `INIT_CAPABILITY(carrier=1, capability_receiver=X_1)` |
| 6 | `INIT_BODY(slot=0, complete slot-0 record)` |
| 7 | `INIT_BODY(slot=1, complete slot-1 record)` |

Irrelevant old fields are absent: `INIT_OWNER.owner_old=255`, `INIT_SEMANTIC.epoch_old=255`, and
nonmeaningful `old_need=0`.

## 3. Adapter timing and laws

For every token: validate; apply the opportunity-boundary operation; update adapter state; emit four
post-update bytes; expand them LSB-first to 32 channels; append them after the 136 primitive
channels; run the common network. No adapter reads reward or settlement outcome.

### 3.1 RAW-GRU

RAW state is a nontrainable uint8 FIFO `R=[255,255,255,255]`. For each valid token, scan present
byte positions `0..15` in increasing order and append each value. If the flag mask is nonzero,
append the packed flag byte as virtual position 16 even when zero. Append means
`R=[R1,R2,R3,value]`. Absent fields are skipped; 254 and duplicates are appended; there is no
deduplication, receiver lane, event-family lane, XOR, equality, hash, or special collision rule.
Emit post-update R.

| Kind | Literal append order | Emitted bytes |
| --- | --- | --- |
| `INIT_OWNER` | kind, subject, owner_new, position | kind, subject, owner_new, position |
| `INIT_SEMANTIC` | kind, subject, epoch_new, position, flags | subject, epoch_new, position, flags |
| `INIT_CAPABILITY` | kind, carrier, capability_receiver, position | kind, carrier, capability_receiver, position |
| `INIT_BODY` | kind, slot, carrier, body_owner, body_epoch, addressed, payload_source, position, flags | addressed, payload_source, position, flags |
| `OWNER` | kind, subject, owner_old, owner_new, opportunity, position | owner_old, owner_new, opportunity, position |
| `SEMANTIC` | kind, subject, epoch_old, epoch_new, opportunity, position, flags | epoch_new, opportunity, position, flags |
| `CAPABILITY` | kind, carrier, capability_receiver, opportunity, position | carrier, capability_receiver, opportunity, position |
| `BODY` | kind, slot, carrier, body_owner, body_epoch, addressed, payload_source, opportunity, position, flags | payload_source, opportunity, position, flags |
| any family NOOP | kind, opportunity, position | `R3_before`, kind, opportunity, position |
| `DECISION` | kind, target, slot, carrier, body_owner, body_epoch, addressed, payload_source, capability_receiver, opportunity, position, flags | capability_receiver, opportunity, position, flags |
| `SETTLEMENT` | kind, opportunity, position | `R3_before`, kind, opportunity, position |

### 3.2 STRUCT-CURRENTNESS-GRU

State `S=[O0,O1,E0,E1]` starts all 255. INIT_OWNER/OWNER for receiver `r` writes `S[r]`; INIT_SEMANTIC/
SEMANTIC writes `S[2+r]`; all other tokens do not write. A decision for target `r` emits
`[S[r], S[2+r], S[r] XOR body_owner, S[2+r] XOR body_epoch]` with ordinary uint8 bitwise XOR and no
Boolean reduction. Every nondecision token emits `[S0,S1,S2,S3]`. A decision missing target/body
OWNER/body epoch is invalid rather than sentinel-repaired.

### 3.3 PI-GRU

State `P=[C0,A0,C1,A1]` starts all 255. Exactly once per opportunity, before processing the token at
position 0, set `A_r=255` if `C_r=255`, otherwise `A_r=min(255,A_r+1)`. No increment occurs during
preamble, decision, or settlement. After that increment, INIT_BODY or realized BODY addressed to
`r` writes `C_r=body_content, A_r=0`; neutral bodies store content 0. A body repeated inside DECISION
does not update PI. PI retains no neutral flag, OWNER, epoch, carrier, slot, or payload source. Emit
`[C0,A0,C1,A1]` on every token. Thus a preamble body has age 1 at the first decision unless
overwritten in opportunity zero; a same-opportunity body has age 0.

### 3.4 DERANGED-CURRENTNESS-GRU

State `D=[D0,D1,D2,D3]` starts all 255. Fixed writes are `O0->D3`, `O1->D2`, `E0->D1`, `E1->D0`.
At a decision for target `r`, emit
`[D[r], D[2+r], D[r] XOR body_owner, D[2+r] XOR body_epoch]`; otherwise emit `[D0,D1,D2,D3]`.
STRUCT and DERANGED each make one byte write on OWNER/semantic tokens, none otherwise, four reads on
nondecisions, and four reads plus two XORs on decisions. Width, event/work count, operation count,
memory traffic, and downstream network are identical.

## 4. Counter-addressed randomness

Canonicalize an address as UTF-8 JSON array with `ensure_ascii=true`, separators `(',',':')`, only
strings/integers, and no NaN/Infinity. SHA-256 it; take digest bytes `0..7` as an unsigned big-endian
`u64`; define `U=(u64+0.5)/2^64`. For unbiased integer `[0,n)`, set
`limit=floor(2^64/n)*n` and increment the address's final retry integer until `u64<limit`, then use
`u64 mod n`. Permutations use descending Fisher-Yates with this integer law. No other digest bytes
are reused.

Environment/initial draws use:

```text
["CBSC-OMRC-B01","ENV",run_name,seed,split,episode_id,
 opportunity_id,family,draw_label,draw_index,retry]
```

Use `opportunity_id=-1` for preamble. `run_name` is exactly one of the three B0/B1/B2 names;
`split` is `TRAIN`, `EVAL_STOCHASTIC`, or `EVAL_MOTIF`.

Other addresses are:

```text
["CBSC-OMRC-B01","ACTION",run_name,seed,"TRAIN",episode_id,opportunity_id]
["CBSC-OMRC-B01","PARAM",seed,logical_parameter_name,row_major_flat_index]
["CBSC-OMRC-B01","ORDER",run_name,seed,rollout_update,ppo_epoch,
 fisher_yates_position,retry]
```

No common address contains arm. Evaluation checkpoint is absent from tape addresses, so every
checkpoint sees identical roots.

Initialization labels are `OWNER_PERM, EPOCH_PERM, NEED_0, NEED_1, CAPABILITY_0, CAPABILITY_1,
BODY_0_ADDRESS, BODY_0_CARRIER, BODY_0_ROLE, BODY_1_ADDRESS, BODY_1_CARRIER, BODY_1_ROLE`.
Every opportunity has fixed addresses for `EVENT_PERM, OWNER_OCCURS, OWNER_SUBJECT,
SEMANTIC_OCCURS, SEMANTIC_SUBJECT, SEMANTIC_NEW_NEED, CAPABILITY_OCCURS, CAPABILITY_CARRIER,
CAPABILITY_RECEIVER, BODY_OCCURS, BODY_SLOT, BODY_ADDRESS, BODY_CARRIER, BODY_ROLE, DECISION_SLOT,
DECISION_TARGET_MATCH, DECISION_GATED, DECISION_ACTIVE`, even when the event does not realize.

Occurrence thresholds are `0.20/0.20/0.25/0.50`; binary choices are zero iff `U<0.5`. Body role is
CORRECT below 0.50, SWAPPED in `[0.50,0.75)`, otherwise NEUTRAL. Decision target matches the
presented body's addressed receiver below 0.65, otherwise the other receiver. GATED is below 0.50;
request active is below 0.85. Permute the four event families independently per opportunity and
generate the decision only after emitting them all.

## 5. Common recurrent PPO

Actor order is `WAIT, SERVE, REFRESH, SAFE_FALLBACK`. Only WAIT is legal off decisions; select it
deterministically, consume no action uniform, and apply no actor/entropy loss. At decisions, mask
WAIT, compute legal FP32 log-softmax, cast the three probabilities to float64, renormalize, and use
the common action U to select the first cumulative probability strictly greater than U; last legal
action is fallback. Store the selected action's FP32 log-softmax. Evaluation greedily selects the
first maximum in order SERVE, REFRESH, SAFE_FALLBACK.

The common FP32 network is `168 -> Linear(128) -> ReLU -> GRU(128) -> actor(4), value(1)`, exactly
121,349 active parameters. Mixed precision, TF32, stochastic rounding, dropout, and arm-specific
normalization are forbidden. For an ordinary matrix entry, initialize
`w=(2*U(PARAM)-1)*sqrt(6/(fan_in+fan_out))`, then cast once to FP32. Units are input `128x168`, each
GRU input/hidden gate `128x128`, actor `4x128`, and value `1x128`. Input columns `136..167` are exact
positive zero and never initialized. All biases, Adam moments/counters, and `h_0` are exact zero.

Authoritative GRU gate order/equations are:

```text
r = sigmoid(W_ir x + b_ir + W_hr h + b_hr)
z = sigmoid(W_iz x + b_iz + W_hz h + b_hz)
n = tanh(W_in x + b_in + r * (W_hn h + b_hn))
h_next = (1-z) * n + z * h
```

For main seeds, train episodes are `0..383`; rollout update `u=0..47` consumes episodes
`8u..8u+7`. Each rollout is eight complete 152-transition episodes. Compute GAE independently per
episode with terminal bootstrap zero and no truncated BPTT. During every epoch recompute recurrence
from `h_0=0`; do not inject detached rollout hidden states.

Normalize decision-transition advantages once over the rollout's 192 decisions using population
variance and epsilon `1e-8`; reuse it for all four epochs. Per epoch, permute eight episode indices
with ORDER addresses, split into four consecutive two-episode minibatches, and take one Adam step per
minibatch: 48 rollouts, four epochs, four minibatches, 768 steps per arm/seed. Actor clipping and
entropy average decisions only; plain unclipped value MSE uses all transitions. Total loss is clipped
actor surrogate `+0.50*value_MSE -0.01*decision_entropy`.

Fixed values remain `gamma=1`, GAE lambda `0.95`, clip `0.20`, Adam `lr=3e-4`, betas
`(0.9,0.999)`, epsilon `1e-8`, zero weight decay, global gradient cap `0.5`. No schedule, value
clipping, reward normalization, auxiliary loss, early stop, checkpoint selection, or arm-specific
optimizer is permitted.

## 6. Fixed 32-episode motif panel

Let motif `m=0..7`, receiver `r=0,1`, slot `s=0,1`, and `tape_id=4m+2r+s`; publish/evaluate IDs
`0..31`. Every episode uses the ordinary preamble. For `m=0..6`, `q=0..11`, A opportunity `2q`, B
opportunity `2q+1`, and carrier `c=q mod 2`.

Notation: `O0/S0/C0/B0` are family NOOPs; `O+(r)` OWNER change; `S+(r)` semantic change with
`new_need=1-old_need`; `C+(c,x)` binding write; `B+(s,c,r,role)` body overwrite; and
`Q(s,r,mode,active)` decision. Missing families emit their NOOP, and every decision has settlement.
Every B+ uses the indexed slot/carrier/receiver; every Q presents that slot to that receiver.

| m | Motif | A opportunity | B opportunity |
| ---: | --- | --- | --- |
| 0 | OWNER change/no change | `[B+(CORRECT),O0,C+(c,r),S0]; Q(GATED,active)` | replace O0 with `O+(r)` in identical order |
| 1 | semantic change/persist | `[B+(CORRECT),S0,C+(c,r),O0]; Q(GATED,active)` | replace S0 with `S+(r)` in identical order |
| 2 | capability OPEN/GATED | `[O0,S0,C+(c,1-r),B+(CORRECT)]`; OPEN active | same sequence; GATED active |
| 3 | correct/swapped | `[O0,S0,C+(c,r),B+(CORRECT)]`; GATED active | replace body with SWAPPED |
| 4 | active/inactive | `[O0,S0,C+(c,r),B+(CORRECT)]`; GATED active | same sequence; GATED inactive |
| 5 | OWNER/body order | `[O+(r),B+(CORRECT),C+(c,r),S0]`; GATED active | `[B+(CORRECT),O+(r),C+(c,r),S0]`; GATED active |
| 6 | semantic/body order | `[S+(r),B+(CORRECT),C+(c,r),O0]`; GATED active | `[B+(CORRECT),S+(r),C+(c,r),O0]`; GATED active |

For `m=7`, divide opportunities into three eight-step blocks `b=0..2`, `base=8b`, `c=b mod2`:

- `base+0`: `[O0,S0,C+(c,r),B+(s,c,r,CORRECT)]`; GATED inactive setup;
- `base+1`: all four NOOP; GATED active designated gap-1 decision;
- `base+2..5`: all NOOP; GATED inactive fillers;
- `base+6`: all NOOP; GATED active designated gap-6 decision;
- `base+7`: all NOOP; GATED inactive.

Only `base+1` versus `base+6` is the retention-gap diagnostic. At every checkpoint evaluate 32
`EVAL_STOCHASTIC` episode IDs `0..31` and the 32 motif tape IDs `0..31`. Reuse the same 64 tapes at
updates `0,12,24,48`. Report stochastic and motif summaries separately; a labeled combined view is
allowed but not an unlabeled replacement estimand.

## 7. B0/B1/B2 bindings

`CBSC-OMRC-B0-INSTRUMENT`, seed 21001, uses TRAIN episode IDs `0..7`, one rollout update, four epochs,
four two-episode minibatches per epoch, and 16 Adam steps per arm. Before updates, the untrained pass
supplies update-zero action/logit/mask/state/adapter checks. After one update, evaluate four stochastic
IDs `0..3` and motif IDs `0,12,20,28`. This is exactly 16 episode executions per arm, has no
scientific branch or selection authority, and contributes nothing to B1/B2. Repair uses a new
create-only B0 attempt identity preserving the failed record.

B1 uses only seeds `21101,21121,21143`; B2 uses only `21161,21179` and only under the existing
stability-extension condition. Per arm/seed: 384 train episodes, 48 rollouts, 768 Adam steps,
checkpoints `0,12,24,48`, and 64 held-out episodes per checkpoint. All previous maximum exposure,
endpoint, RAW-competence, branch, and stop laws in `DIRECTION.md` remain unchanged.

## 8. Checkpoints, publication, and resources

Save B1/B2 checkpoints after exactly `0,12,24,48` completed rollouts; B0 saves update zero and after
its one rollout. Each checkpoint includes all network bytes, Adam moments/counters, object/run/arm/
seed/update identity, and parameter-init, train-tape, action-uniform, minibatch-order, and config
digests. Adapter state and recurrent hidden state are episode-local and are not checkpointed.

Authoritative result schema: `cbsc_omrc_b01_b_explore_result_v1`. Each run manifest includes object
and clarification IDs, run and implementation/evidence refs, config and environment/adapter/token
digests, arms/seeds/checkpoints, all interaction/update/evaluation counts, every seed curve and
return/regret, all currentness/action diagnostics and 32 motif records, RAW competence, parity and
numerical audits, resource admission/peak RSS, incidents, applicable B branch, and exact claim
ceiling. B1 and B2 have distinct manifests; B2 may reference but never replace B1.

Publication is create-only: write a fresh temporary run directory, validate completeness/digests/
audits, write the manifest, flush files and directory metadata, then atomically rename to a fresh
final identity. Collision is an incident; never overwrite. Partial, truncated, resource-stopped,
nonfinite, or parity-failing attempts publish incident-only and have no scientific branch.

Immediately before initializing every B0 arm or B1/B2 arm-seed process, require both OS physical
available memory and effective container/cgroup headroom to be at least 4 GiB through the repository
preflight. Per invocation caps are:

| Resource | B0 arm | B1/B2 arm-seed |
| --- | ---: | ---: |
| Wall time | 30 minutes | 120 minutes |
| Peak host RSS | 4 GiB | 4 GiB |
| Scratch | 2 GiB | 2 GiB |

The whole object's create-only durable output cap is 512 MiB. A cap hit is no observation and no
consumed B run. A fresh named attempt may improve vectorization, layout, or compression while
preserving laws and incident evidence. Concurrent processes must each pass effective-headroom
admission; all arms within a seed use the same device class and FP32 mode.

## 9. CM-owned degrees and interpretation

Only module/class organization, scalar versus vectorized execution, CPU versus GPU under within-seed
device/FP32 parity, scheduling/sharding, logging, compression/container format, filenames below the
run root, progress UI, plotting, and episode-local cache layout are delegated. They must be fixed
before an attempt, symmetric, recorded, and meaning-preserving. Low-level kernels need not be
bit-identical across hardware, but the mathematical initialization, GRU, action, PPO, tape, adapter,
and within-seed parity laws must match this specification.

No material comparator or support ambiguity remains. RAW retains every primitive token and is not
information-deleted; STRUCT/DERANGED work is exact; PI age and neutral semantics are single-valued;
NOOP, initial bodies, causal order, supports, recurrent recomputation, normalization, masking, and
sampling are bound. No adapter receives semantic Booleans, validity, reward, success, oracle action,
future facts, or extra interaction.

The surviving alternative is scientific: any STRUCT advantage may reflect finite-budget
conditioning or optimization rather than representation necessity. The falsifier remains competent
RAW matching/beating STRUCT without predicted currentness corrections, or DERANGED producing the
same return/twin effect. The maximum claim remains a preliminary signal, null, instability,
generic-conditioning explanation, predictive-index sufficiency observation, or counterexample on
this host. Exact-factorial and `CBSC-LR01=UNRESOLVED` meanings do not change.

## Evidence

- `DIRECTION.md`
- `CBSC_OMRC_B01_CM_IMPLEMENTATION_CONTRACT.md`
- `CBSC_OMRC_B01_INNOVATOR_INTAKE_20260901.md`
- `temp/sessions/hmasd-chatgpt-pro-transport/archive/capability_bound_semantic_currentness/cbsc-online-b-innovator-20260901-02/RESPONSE.md`
- `temp/sessions/hmasd-chatgpt-pro-transport/archive/capability_bound_semantic_currentness/cbsc-online-b-innovator-20260901-02/TRANSPORT_FACTS.json`
