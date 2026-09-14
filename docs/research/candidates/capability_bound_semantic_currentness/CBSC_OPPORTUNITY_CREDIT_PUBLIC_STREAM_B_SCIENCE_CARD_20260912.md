Claim: one future paired training run would test whether STRUCT improves final native return beyond same-information RAW under the existing sampled opportunity-credit package.
Binding structure: systems / information flow.

# CBSC opportunity-credit public-stream B candidate — 2026-09-12

**Prospective B/EXPLORE description; S preparation only. Not an implemented,
runtime-accepted, funded or frozen scientific invocation.** Portfolio selected
one preparation cycle in response `86428c9e87fc4c61888b5638781603038c39399d`,
[§3](../../portfolio/pro_packets/20260912_resume_five_independent_chains/archive/RESPONSE.md).
The [S mapping](../../portfolio/pro_packets/20260912_resume_five_independent_chains/EXECUTION_MAPPING.md#s--cbsc-one-preparation-cycle)
buys this card/L0 and its [readiness intake](CBSC_PUBLIC_STREAM_S_READINESS_INTAKE_20260912.md).
A new unscreened seed, outer object identity, source and invocation budget would
be bound only in a later selected task; old B04/B05/P47 identities are not reused.

This host has one learning controller and two receiver environment entities.
Currentness is an inspiration for information flow under multi-agent partial
observability; this experiment would not measure multi-agent learning, roster
change or partner co-adaptation.

## Question, comparison and interpretation

Keep the question and scientific recipe of
[B04](CBSC_OPPORTUNITY_CREDIT_B04_SCIENCE_CARD_20260906.md): after 48 real
eight-episode rollouts, does STRUCT-CURRENTNESS-GRU improve native return over
RAW-GRU, and how do both compare with the public REQUEST_ONLY rule?
Both arms use fresh matched initialization and common exogenous/action-uniform/
minibatch addressing; matched sources do not force identical actions.
The primary is the mean of **all 32 final update-48 STRUCT minus RAW episode
returns**, retaining every signed difference, absolute return and both
checkpoints. One complete paired training instance is the independent unit;
32 evaluation episodes and the update-0 context are not training replications.

Retain MEI **0.25 native episode return**, the existing practical scale.
Above +0.25 would be a local useful representation-package signal; inclusive
±0.25 leaves practical separation unresolved with its sign retained; below
−0.25 is adverse. A missing primary has no paired polarity. RAW/STRUCT gaps
remain limited when either loses to REQUEST_ONLY. Two older zero comparisons
and RAW B04's 12.0375 below REQUEST_ONLY 12.375 are retained counterevidence.
The DM weakly expects a gap inside MEI, with low confidence; this is an
unscored prospective expectation, and the owner prediction is not taken.
No result is claimed by S. No stable superiority, semantic necessity,
causal attribution to the target, general MARL or UAV claim is contemplated.

Headroom: no matched tuned same-information baseline/upper record is available.
REQUEST_ONLY is useful context, not tuned headroom. The historical exact/LR01
hosts and budgets do not supply that record. Its absence does not hold a B.

## Scientific recipe held fixed

- Unchanged dynamic-cache host: two receivers, 24 opportunities and 152 tokens;
  public events/state/RNG law and delayed native settlement remain. Public
  OWNER/semantic events → receiver history → RAW or deterministic STRUCT
  features → sampled action → its own decision and next settlement rewards →
  recurrent updates → held-out native return.
- Same complete legal public stream plus four-byte RAW FIFO, or the same stream
  plus deterministic four-byte STRUCT. No VALID, hidden truth, oracle action,
  future event or unchosen reward enters the learner.
- Same 168→Linear128/ReLU→GRU128→actor4/value1 model, 121,349 parameters,
  original adapter-column zero initialization, CPU FP32 and one compute thread.
  PPO clip .20, entropy .01, value coefficient .50, Adam 3e-4,
  betas (.9,.999), epsilon 1e-8, weight decay 0 and gradient cap .5 remain.
- At t=12+6q, G=stop-gradient(r[t]+r[t+1]); subtract detached old decision
  value. Normalize once over all 192 decisions with epsilon outside the square
  root. Four fixed PPO epochs reuse those targets/advantages; the critic fits
  unnormalized G on decision rows only. Keep full 152-token episode BPTT,
  original minibatch/action addressing and Adam order, including final settlement.
- Train IDs 0..383 once per arm; evaluate greedily with fresh episode recurrence
  only at updates 0 and 48 on 32 separate, common stochastic evaluation tapes.
  Score ALWAYS_REFRESH, ALWAYS_SAFE and REQUEST_ONLY once on those same tapes;
  REQUEST_ONLY reads the public request flag before evaluator access.
  Retain original sampled-action/credit/exposure records and actual checkpoint
  state. No best endpoint, extra panel, tuning, rollout reuse or policy search.

## One candidate and its L0

**Goal:** a narrow direct-public-byte boundary around the existing host/learner,
described here for later investment. It is an alternative candidate, not an
attributed production repair. Scientific source inspected as data is
`6268d6638`; paths below are relative to
`experiments/candidates/capability_bound_semantic_currentness/`.

| Boundary | Concrete prospective route and source support |
| --- | --- |
| Host and event ownership | Reuse `omrc_b01/host.py` `DynamicHost.build_stochastic`, its initialization/potential/directive/state/addressing law. A local subclass would override **only `_finish`**; no module monkey-patch or replay of retained52. |
| Token storage | In that finish, read the 16 public fields in `token.py`'s explicit order and form the last byte from its eight Boolean flags in bit order. Store one owned immutable 17-byte row per token. Preserve literal masks, sentinels, chronology and domain meaning directly. An explicit small tape record holds identity/public rows and a separate evaluator view; it does not run `EpisodeTape.__post_init__`'s canonical repack. |
| RAW | From each public row, append bytes 0..15 selected by the existing literal bmask in ascending index order, then the complete flag byte when fmask is nonzero; retain the last four bytes, initially 255. This is `adapters.py:RawHistoryAdapter.process`'s exact FIFO law, not the last four raw bytes of every token. |
| STRUCT | Maintain owner/epoch registers per receiver, initially 255. INIT_OWNER/OWNER set owner from public owner_new; INIT_SEMANTIC/SEMANTIC set epoch_new. At DECISION emit target owner, target epoch, owner XOR body_owner, epoch XOR body_epoch; otherwise emit the four registers. No truth dependency is added. |
| Projection | Expand each public 17-byte row plus the four adapter bytes LSB first into a newly owned CPU FP32 tensor, 152×168 per episode and batch 8×152×168. Avoid `LearnerProjection.float32_channels`, NumPy observation buffers/`torch.from_numpy`, and `engine._project_panel`'s automatic duplicate replay. Preserve feature values/order and episode adapter reset. |
| Learning | Reuse `engine._rollout_from_panel`, `_training_action_uniforms`, `_evaluate_heldout`, the existing model and `opportunity_credit_b04/learner.py`. They consume the observations and a tape identity/evaluator interface; full recurrence and sampled credit remain. |
| Native primary | Existing `evaluate_episode` requires an actual `EpisodeTape`; the new record cannot silently pass that interface. A small native-record function would use the unchanged `EpisodeEvaluator.ledger`/native ledger for the **already chosen** 24 actions, preserve separate decision/settlement contributions, and publish the same exact totals. It need not compute unused oracle/regret fields. Update the caller explicitly. |
| Publication | Adapt the small B04 direct runner to the new outer identity and tape/project/native-record calls; reuse `snapshot.py:snapshot_readback` with truthful metadata and the complete final pairing/readback contract of `run.py`. No old checkpoint or incomplete result is relabelled. |

**Owned paths:** S owns only this card, intake, computed documentary facts and
necessary owner/audit records in the shared Windows `codex/cbsc` checkout.
A later implementation, if selected, could be limited to a direction-local
`opportunity_credit_b04/direct_public.py`, its direct runner and one CLI;
these are proposed paths, not files created or authority to edit them now.
Preserve old source/evidence and the B04/B05/P47 records.

**Acceptance and remaining facts:** the source mapping supports a reviewable
candidate. It does **not** demonstrate runtime independence: host constructors,
`PrimitiveToken` validation, Enum/Fraction objects, imported libraries, model
initialization (including its NumPy use), optimizer and process runtime remain
shared. No corrupting writer is identified. A later selected implementation
would require focused evidence for the changed public-byte/adapter/reward/output
boundary and independent review of that actual high-risk diff under
Engineering Scope §7.3; S purchases neither. No all-history reconstruction,
new architecture audit or prior positive result is required. The remaining
facts are actual changed-path behavior, same-information/reward correctness,
complete primary publication, runtime binding and complete cost.

**Budget and stop:** S has zero implementation, target imports, tests/fixtures,
models, scientific RNG, learner/evaluation or remote runtime calls; one
documentary cycle, complete invoked support≤600 s with 300 s as reference.
Engineering Scope §4 needs **none**. End on publication of this candidate and
its limitations. S+B, a second cycle and a new consultation are unallocated.

## Known work and unknown cost of the offered future comparison

[Computed facts](CBSC_PUBLIC_STREAM_S_FACTS_20260912.json) use configuration
arithmetic only. Per arm: 384 training episodes / 58,368 transitions /
9,216 decisions / 768 Adam steps; 64 update-0/48 evaluation executions /
9,728 transitions. Pair: 116,736 training plus 19,456 evaluation transitions,
1,536 Adam steps and 128 evaluations. Three rules add 96 same-tape ledger
passes / 2,304 chosen-action scores, not new worlds.

Dominant intrinsic work is 2 arms×1 paired seed×48×8 full 152-token rollouts,
2×48×4×4 minibatch updates with full recurrent backward passes, and 2×2×32
evaluations. Generating 384+32 distinct tapes produces 63,232 public tokens
per arm; projecting each once expands 10,622,976 feature values per arm.
Existing automatic duplicate projection is validation work, not extra
scientific exposure. Removing it predicts no measured runtime saving.

The previously offered 600 s/arm, 1,200 s native sum, 600 s support including
S and 1,800 s complete chain remain **unallocated ceilings**, not estimates
or balances. Required startup/admission, construction, learning, evaluations,
publication/readback and exit belong to each complete arm; support includes
preparation/check/review/staging/monitor/intake/integration/cleanup once.
Actual candidate cost and support after S remain unknown. Any later selected
run would bind source/runtime on the current remote route with CPU FP32,
one thread and fresh destination admission; no runtime change or launch occurs
here. Full documentary/deliberation cost remains separately unknown.
