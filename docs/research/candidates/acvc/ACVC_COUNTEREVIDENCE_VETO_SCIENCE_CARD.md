# ACVC B1 counterevidence-binding science card

Owner: `direction:acvc-counterevidence-veto` Explorer Manager  
Candidate: `CAND-ACVC-COUNTEREVIDENCE-VETO`  
Treatment identity: `ACVC-B1-LEARN-CORRECT-v1`

The prior VSP-05 real-toy result produced alias-only support and no TARGET-versus-SHAM
separation; it is background, not evidence for this direction. See
[`REAL_TOY_SEMANTIC_VETO_CODE_SCIENCE_INDEX.md`](../vsp_05/REAL_TOY_SEMANTIC_VETO_CODE_SCIENCE_INDEX.md)
and its linked result. ACVC asks a new prospective question in a constructed host.

## Scientific question and comparison

In the four-target host below, can a zero-initialized tabular receiver trained only
from return learn to use a truthful negative verdict selectively when the verdict is
correctly bound to `(event_id, subject_epoch, target_id, predicate,
validity_window)`, relative to the same learner trained with a prospective random
reassociation of exactly the same verdict payloads and binding tuples? Selective use
means that the receiver does not complete the invalid target while invalid, does not
spread caution to co-occurring clean targets, repairs a repairable invalid target,
and abstains from a terminal invalid target.

- Treatment, `LEARN-CORRECT`: each verdict payload is attached to its own complete
  binding tuple.
- Primary comparator, `LEARN-PERM`: before learning, each scene receives an
  independent uniform permutation over all 24 four-slot permutations, including the
  identity. Verdict payloads are reassociated with permuted complete binding tuples
  and the resulting frames are re-authenticated. The displayed negative target is
  therefore uniform and independent of the true invalid target, not predictably
  wrong.
- Both arms use the same learner, initialization, paired latent scenes, budgets, and
  random-number namespaces. The estimand is the total effect of learning and acting
  under correct versus randomized semantic association. It is not a binding-versus-
  no-message estimand.

The strongest alternative is `DET-BOUND`, a deterministic exact-match rule that
uses the same correct binding, continues once on a matching negative, completes
after an epoch increment, and otherwise abstains. It is analytically sufficient in
this truthful host. A successful learned arm can therefore establish learnability
and selective use of bound evidence, but never the necessity or superiority of
adaptive learning. The strongest binding-free alternative is `AUTH-PROBE`, which
uses the mere presence of an authenticated negative to search all targets.

## Observable and when scientific activity begins

The scene is the randomization and analysis unit. On true-event test scenes, let
`Y` be undiscounted total scene reward, including all target outcomes, action costs,
and the fixed communication cost. For each of ten paired base seeds, compute the
mean over that seed's paired event scenes and then

`tau_neg = mean_seed(Y_LEARN-CORRECT - Y_LEARN-PERM)`.

Report a two-sided 95% Student-t interval over the ten seed-level paired effects.
Also report all reward components, the three fixed-policy references, and these
seed-level rates:

- `false_complete`: an invalid target is completed while invalid;
- clean-target harm `1 - clean_target_return`, excluding the shared communication
  cost, separately on all-clean scenes and clean targets inside event scenes;
- `D_joint`, which is one on an event scene only when the invalid target is never
  completed while invalid, every clean target is completed on its first action with
  no probe/continue/abstain, a repairable invalid target is continued exactly once
  and then completed, and a terminal invalid target is continued exactly once and
  then abstained.

Question-relevant scientific activity starts only when a final frozen checkpoint
from each learned arm has produced the first complete paired held-out true-event
scene with both scene rewards and target-level action/outcome rows. Training logs,
unit checks, launcher activity, serialization, and an unpaired or all-clean-only
evaluation are not question-relevant output. Failure before this criterion is
engineering provenance, not evidence against the treatment or direction.

## Host, dynamics, and rewards

- One scene contains four exchangeable targets. At reset, every target exposes the
  identical executor evidence `local_done=1` and `local_confidence=230/255`.
- Half of scenes are all-clean. In the other half, one uniformly chosen target has a
  latent invalidating event fixed before binding assignment or receiver action; its
  local positive is an alias. Event subtype is exactly half `repairable` and half
  `terminal`.
- Each target has a unique nonzero opaque `target_id:u64`, opaque
  `audit_event_id:u64`, and base `subject_epoch:u32` sampled in
  `[1, 2^32-2]`. Values are freshly randomized per scene and are not learner
  features. A repair increments only that target's epoch by one.
- Target service order is uniform over all 24 orders and independent of event target,
  subtype, IDs, and binding permutation. Receiver state resets at scene start;
  `event_located=false`, replay cache is empty, global decision tick is 1, and each
  target's action count starts at zero.
- The receiver services one target at a time. A terminal action moves to the next
  target. Each target permits at most three actions; if the third action is not
  terminal, forced abstention is scored from the then-current latent state. A scene
  therefore has at most 12 decision transitions.
- Actions and immediate rewards are:
  - `complete`: `+1.00` when currently valid; `-10.00` and
    `false_complete=1` when invalid;
  - `continue`: `-0.10`; on a repairable invalid target it clears invalidity and
    increments the epoch, while on a valid or terminal-invalid target it leaves the
    state unchanged;
  - `probe`: `-0.25` and reveals exactly one of `valid`,
    `invalid_repairable`, or `invalid_terminal` for the current target;
  - `abstain`: `+0.20` for terminal invalidity and `-0.80` for a valid or repairable
    target. Forced abstention uses the same payoff.
- Terminal-action scoring precedes horizon handling. `complete` is scored against
  pre-action validity; no same-tick expiry or repair can rescue an invalid
  completion. Rewards are undiscounted and summed across targets. Communication
  subtracts `0.04` once per scene.

## Certificate schema and binding intervention

Before decision tick 1, fixed `certifier_0` emits four frames, one for each target.
Every event scene has exactly one `verdict_bit=1`, on the true invalid target before
the arm intervention; the other three bits are zero. Every all-clean scene has four
zero bits. Confidence is always 242. Four frames, 256 bytes, one sender, one delivery
time, and the same communication debit occur in every arm.

Each frame is exactly 64 bytes. Unsigned integers are little-endian and fields occur
in this order:

| Field | Bytes | Frozen meaning |
|---|---:|---|
| `version:u8` | 1 | `1` |
| `sender_id:u16` | 2 | `0` (`certifier_0`) |
| `verdict_bit:u8` | 1 | zero or one as above |
| `confidence_u8:u8` | 1 | `242` |
| `predicate:u8` | 1 | `1 = TARGET_INVALIDATES_COMPLETION` |
| `event_id:u64` | 8 | target's audit-event context |
| `subject_epoch:u32` | 4 | current target epoch at issuance |
| `target_id:u64` | 8 | target identity |
| `valid_from:u32` | 4 | `1` |
| `valid_until:u32` | 4 | `12`, inclusive global decision tick |
| `sequence:u32` | 4 | unique random nonzero value within the scene |
| `reserved` | 10 | all zero |
| `auth_tag` | 16 | host-issued opaque integrity/provenance tag |

Authentication is a host oracle for recognized provenance and intact bytes. It does
not model cryptographic strength, forgery resistance, or issuer truth under
compromise. Sequence values, frame display order, and tags are drawn independently
of world state and permutation. Raw ID, sequence, display-order, and tag bytes are
not learner features; only verification and semantic equality results are exposed.

For slot `j`, let `B_j` contain the five-field binding and let `P_j` contain verdict
and confidence. `LEARN-CORRECT` emits `(B_j,P_j)`. `LEARN-PERM` draws hidden
`pi` and emits `(B_pi(j),P_j)`, with a fresh valid tag over the final bytes. Frame
display order is independently shuffled. Across arms the multisets of bindings,
payloads, confidences, approved senders, accepted frames, timing, byte counts,
sequences, and costs are identical; only payload-to-world association differs.

Frame interpretation uses this precedence:

1. Reject wrong length or version.
2. Reject failed authentication or an unapproved sender.
3. Reject a duplicate sequence within the scene.
4. Require exact `event_id`, current `subject_epoch`, `target_id`, and predicate.
5. Require current tick inside the inclusive validity window.
6. Only then may `verdict_bit=1` set `active_matching_negative`.
7. A matching negative takes precedence over the local positive in the derived
   observation, but all four actions remain available.
8. A repair-induced epoch increment makes the old frame nonmatching before the next
   decision.

All registered experiment frames are well formed and authenticated. Parser failure
cases are technical checks and do not add scientific cells.

## Receiver observation and learner

The host observation contains the current local positive/confidence, current target
IDs and audit context, current epoch, global tick, target action count, service
position, previous probe/continue feedback, all parsed frames, and equality/in-window
indicators for the five binding fields. It never contains latent validity, subtype,
arm, permutation, or certifier-private state.

The tabular learner's canonical state is exactly
`(service_position, target_action_count, previous_feedback,
any_authenticated_negative, active_matching_negative, event_located)`, where
`previous_feedback` is one of `none`, `probe_valid`, `probe_repairable`,
`probe_terminal`, `continue_epoch_changed`, or `continue_no_change`.
`event_located` becomes true only after a probe reports an invalid target or a
repair transition increments an epoch; it persists for the scene and resets for the
next scene. `previous_feedback` resets to `none` when service moves to a new target.
Opaque numeric values and frame order are excluded.

For every base seed and arm, initialize all Q values to zero. Use ordinary tabular
Q-learning with `gamma=1.0`, constant `alpha=0.15`, and epsilon-greedy exploration:
epsilon falls linearly from `0.30` at training episode 1 to `0.02` at episode 7,000
and remains `0.02` through episode 7,680. Training ties use the paired learner RNG.
Evaluation is greedy; a single fixed action-rank permutation drawn from the learner
seed resolves evaluation ties and is shared by both arms. Each arm updates its own Q
table; no arm label, Q value, transition, or gradient crosses arms. Final episode
7,680 is the prespecified checkpoint. Validation is diagnostic only and cannot tune,
select, stop, or restart training.

## Fixed references and interpretation

- `DET-BOUND` uses correct frames. It completes a target immediately unless an
  active matching negative exists; on a match it continues once, completes after an
  epoch increment, and otherwise abstains. Its analytic mean event-scene return is
  `3.46` and `D_joint=1.0`.
- `AUTH-PROBE` ignores every binding field. When any authenticated negative exists,
  it probes targets in service order until the invalid target is found or only one
  untested target remains, and completes every probed-valid target. If a probe
  reports `invalid_repairable`, it continues exactly once and then completes. If a
  probe reports `invalid_terminal`, it abstains immediately without a continue. If
  the last untested target is inferred invalid without a probe, it continues exactly
  once, then completes if the epoch increments and otherwise abstains. This is the
  utility-optimal authority-only trace under the frozen costs; it is not changed to
  imitate the binding-aware trace merely to satisfy `D_joint`. Its analytic mean
  event return is `2.935` and `D_joint=0.125`.
- `IGNORE` ignores all frames and completes every local positive. Its analytic event
  return is `-7.04`.
- A reporting-only latent oracle sees subtype and has event return `3.51`; unlike
  `DET-BOUND`, it need not pay for a failed continuation on a terminal target.

The information-optimal correct-versus-authority gap is therefore `0.525`. The
registered evidence supports selective learned use only if all of the following
hold over the ten seed-level aggregates:

- mean `tau_neg >= 0.40` and its two-sided 95% lower confidence limit is `> 0.25`;
- the one-sided 95% upper limit on correct-arm invalid false completion is `< 0.01`;
- correct-arm mean clean harm is `<= 0.02` and its one-sided 95% upper limit is
  `< 0.05` in both clean strata;
- correct-arm mean `D_joint >= 0.90`, with one-sided 95% lower limits on paired
  `D_joint` gaps `> 0.40` versus both `LEARN-PERM` and `AUTH-PROBE`;
- the lower 95% limit for `Y_LEARN-CORRECT - Y_DET-BOUND` is greater than `-0.05`.

If the primary difference is positive but clean harm fails, blanket caution rather
than selective use explains the result. If `LEARN-PERM` approaches correct-arm
`D_joint` with negligible clean harm, the randomized association or observation has
a side channel and the binding claim does not follow. If correct learning passes the
binding, safety, and clean criteria but falls materially behind `DET-BOUND`, the
experiment supports the deterministic binding protocol only. No outcome supports a
claim that learning is better than `DET-BOUND`.

## Seeds, counts, and caps

Base seeds are `[11, 23, 37, 53, 71, 89, 107, 127, 149, 173]`. For base seed `s`,
use independent namespaces:

- train world `100000+s`, train binding `200000+s`, learner `300000+s`;
- validation world `400000+s`, validation binding `450000+s`;
- test world `500000+s`, test binding `600000+s`;
- evaluation tie rank `700000+s`.

World RNG owns episode class, true target, subtype, IDs, epochs, and service order.
Binding RNG owns permutations, sequences, frame order, and opaque tags. Exploration
randomness is counter-keyed by seed, episode, service position, and local action
index so paired arms consume the same draw at the same decision coordinate even
after their trajectories differ.

Per learned arm and base seed:

| Split | Episodes | Event / all-clean | Exact event balance |
|---|---:|---:|---|
| train | 7,680 | 3,840 / 3,840 | 20 per `(true_target, subtype, pi)` cell |
| diagnostic validation | 768 | 384 / 384 | 2 per cell |
| held-out test | 3,840 | 1,920 / 1,920 | 10 per cell |

All 24 permutations and all 24 service orders occur equally often within each
episode class and split. Their relative alignment is shuffled with independent
namespaces. The three fixed policies run only on the same held-out test scenes.
There are 245,760 learned-arm scenes and 115,200 fixed-policy test scenes. At 12
decision transitions per scene, the absolute maximum is 4,331,520 transitions.

The real registered process has hard caps of one CPU worker, 5,000,000 decision
transitions, 18 minutes wall time, and 1.5 GiB peak RSS. A cap breach or incomplete
paired output yields no scientific conclusion and is not a negative treatment
result. There is no smoke or reduced-budget scientific run; after construction and
ordinary technical checks, the next execution is the registered real
train/evaluate/analyze flow.

## Claim ceiling and CM construction request

Any supported claim is limited to this constructed synchronous four-target host,
one truthful fixed certifier, at most one invalidating event, stable IDs and epochs,
pre-decision delivery, the stated costs, one tabular learner, ten seeds, and the
registered finite budget. It does not establish cryptographic security, truth under
sender compromise, production prevalence, delayed or concurrent evidence handling,
multiple events, arbitrary completion semantics, deployment value, open-support
generalization, or adaptive-learning superiority over an exact deterministic rule.

CM should construct an isolated host, policies, registered runner, analyzer, and
ordinary deterministic contract tests from this card. Suggested fresh paths are
`experiments/candidates/acvc/{host,policies,run,analyze}.py`,
`tests/experiments/candidates/acvc/test_acvc_b1.py`, and final result
`docs/research/candidates/acvc/ACVC_B1_RESULT.json`; equivalent isolated paths do not
change scientific identity. The result must contain declared/actual counts and caps,
per-seed paired observables and confidence limits, fixed-policy metrics, both clean
strata, `D_joint`, false completions, material anomalies, and whether the stated
scientific-activity criterion was reached. Missing source, adapter, runner, or host
is CM construction work and does not alter or defer the scientific question.

No pre-result Pro request is needed: the recovered analysis already exposes the
answer-changing alternatives and fixes them in controls and the claim ceiling.
