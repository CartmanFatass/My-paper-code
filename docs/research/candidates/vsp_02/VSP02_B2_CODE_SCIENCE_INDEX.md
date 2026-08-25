# VSP02-B2 code-science index

This is the isolated implementation binding for
`VSP02-B2-PAIRED-SHADOW-LEARNER-LOCALIZATION`. It records implementation
evidence only. CPM retains integration, review, runtime admission, the sole
registered full, publication, readiness, and technical acceptance. Explorer
retains the sole scientific intake and successor choice.

```text
treatment=VSP02-B2-PAIRED-SHADOW-LEARNER-LOCALIZATION
candidate=CAND-VSP-02@adversarial-revision-v8
source=experiments/candidates/vsp_02/vsp02_b2_paired_shadow_learner_localization.py
runner=scripts/run_vsp02_b2_paired_shadow_learner_localization.py
tests=tests/experiments/candidates/vsp_02/test_vsp02_b2_paired_shadow_learner_localization.py
index=docs/research/candidates/vsp_02/VSP02_B2_CODE_SCIENCE_INDEX.md
host=VSP02-A2-PHYSICAL-LIFECYCLE-HOST-v1
accepted_precursor_source=89fe924883b3ee768e30126ed51cc49644dfcf72
accepted_precursor_publication=eb2cb349075f369c244f1ae33a434be28c0177e7
resource_class=B_TOY_LIGHT
pool_units=1
formal=false
evidence_search=H=4|K_search=0|hypothetical_transitions=0
arms=RL_ORIGINAL|SUP_TRUE|SUP_FLIP
training=5 units|1024 real RL-generated episodes per unit|128x8|4/4 cue balance per update
updates=128 per arm/unit|1920 total
evaluation=128 common held-out real-host episodes per arm/unit|1920 total|one final checkpoint
hard_caps=145348 transitions|5120 training episodes|1920 evaluation episodes|1920 updates|30 CPU minutes|2 GiB
retry_rescue_sweep_extra_arm_seed_checkpoint=0
implementation_status=SOURCE_READY_FOR_INTEGRATED_REVIEW
```

## Critical protected points

- The accepted host physics are retained while every physical tape receives a
  fresh B2-only identity: source line 89.
- Exact SHA-256 seed derivation, exhaustive stream allow-list, and B1V2
  collision report: source lines 230 and 247.
- Validation reconstructs registered initial GRU/actor/critic tensors directly
  from the local seeded `torch.Generator` in frozen shape/order. It never
  constructs a learner/model and leaves global Torch RNG bytes unchanged:
  source lines 383 through 438 and 2257.
- Fresh, byte-identical parameter/optimizer clones and unchanged float64
  `GRUCell(10,16)` actor/critic forward path: source lines 612 and 629. The
  forward exposes raw softmax separately while training/actions retain the
  accepted one-time `0.1+0.8*q` mixture.
- Deterministic 128-by-8 schedule with exact four/four cue support and retained
  terminal cue-RNG receipt: source lines 661 through 699.
- The RL actor uses detached `G-b`, the two supervised actors use lifecycle CE
  only, and every arm retains `mean(0.5*(G-b)^2)`: source line 722.
- P3 zero-activity proof hashes RL parameters, optimizer, RNG, successor state,
  and immutable batch before/after shadow computation: source line 800.
- P0-P8 construction report binds precursor/source, architecture, optimizer,
  loss/autograd routes, label firewall, schedule, evaluator, and RNG: source
  lines 918 and 1072.
- RL-only real-host collection freezes canonical `O,H0,M_reset,M_active,
  M_valid,M_lifecycle,A_behavior,R,Done,G` before any update: source lines 1171
  and 1234. Each retained batch includes all eight immutable rows, transition
  counts, clone identities, and its canonical digest.
- Per-arm updates use the identical frozen order, global clip 1.0, independent
  optimizers, and no shadow-to-RL mutation: source lines 1308 through 1552.
  Every update retains its exact batch rows, model/optimizer hash chain,
  ordered batch binding, loss/gradient route, shadow-to-RL pre/post receipt,
  final model and Adam state, and terminal RNG receipts.
- Common independently recreated held-out panels, finite raw-softmax `q`,
  exactly one `p=0.1+0.8*q` projection, no stochastic evaluation action, and
  raw/mixed argmax equivalence: source lines 871 and 1556 through 1693. Every
  clone retains finite logits, raw softmax, once-mixed behavior probabilities,
  argmax/action, panel identity, transition count, final-model binding, and
  panel-RNG terminal receipt.
- Ordered terminal classification and exact activity/runtime projections:
  source lines 1998 through 2254.
- Pure retained-result validation reconstructs seeded P2 expectations,
  schedule/panel RNG streams, every host row from the frozen physical law,
  functional GRU logits and gradients, exact Adam equations, all five training
  units, all fifteen final checkpoints, activity/support, P3 chains, raw-q
  metrics, aggregates, runtime contract, branch, and Git source binding: source
  lines 2257 through 3163. It invokes no treatment, host, optimizer, model, or runtime
  evaluator and creates zero additional scientific activity.
- A non-result-bearing bounded deterministic replay fixture exercises one
  registered root, two scheduled minibatches, all three learner/Adam routes,
  and all three exact 128-clone evaluation panels. Its validator performs the
  same pure retained-evidence reconstruction: source lines 1702 through 1958.
- Write-once zero-episode technical proof, exclusive registered-full claim, and
  retained validation entry points: runner lines 130, 146, 170, and 212.
- Mutation tests reject failures in every P0-P8 family and every branch
  precedence edge; dedicated regressions prove the registered ±0.70 gates are
  reachable from raw `q`, reject a second mixture, and reject technical-only
  runtime and missing units. Bounded replay mutations additionally reject an
  altered seeded event, action, observation, reward, behavior probability,
  physical transition, loss, gradient, parameter/Adam transition, final model
  or optimizer state, checkpoint logit, or terminal RNG receipt: test lines
  293 through 357. A call-trap proves both retained validation and the validate
  CLI cannot invoke the treatment, host, optimizer, learner/model, or evaluator;
  it also asserts byte-identical global Torch RNG before/after: test line 359.

## Boundary preserved

`RL_ORIGINAL` alone creates training host episodes and actions. Labels are
constructed from frozen cue metadata only after the forward input and immutable
batch exist; they enter only the supervised lifecycle CE target and post-forward
diagnostics. They never enter observation/state, masks, rewards, returns,
advantages, critic targets, behavior collection, RL loss, or evaluation input.
Each supervised arm is an off-policy shadow conditional on the evolving RL
generator. Therefore a later direct-only result would remain a B2-local
finite-cap learner-path contrast, not evidence of actor-critic incapacity,
fixed-representation sufficiency, the cause of B1V2, temporal-credit or
optimizer causality, sample efficiency, independently on-policy superiority,
architecture superiority, lifecycle value, C, Pro, promotion, or retirement.

## Registered full publication

```text
source_commit=bd0da64f851718cf0b5d59b144d99a7006ff2a73
branch=B2_DIRECT_SUCCEEDED_ORIGINAL_FAILED
aggregates=RL_ORIGINAL(mean_J_eval=0.9397548469844077,mean_kappa=0.003299876010273839,exact_correct_units=0/5)|SUP_TRUE(mean_J_eval=1.3270742974252738,mean_kappa=0.7692414868151642,exact_correct_units=5/5)|SUP_FLIP(mean_J_eval=0.17292570257472628,mean_kappa=-0.7692414868151644,exact_inverse_units=5/5)
activity=environment_transitions=30160|training_episodes=5120|optimizer_updates=1920|evaluation_episodes=1920|checkpoints=15|result_bearing_runs=1
caps=transitions<=145348|training_episodes<=5120|evaluation_episodes<=1920|updates<=1920|retry_rescue_sweep_extra_arm_seed_checkpoint=0
full=one_registered_full|pure_validator=VALID|operator_receipt=temp/sessions/code_project_manager/vsp02_b2_operator_receipt.json
nonclaims=localization-only; no actor-critic incapacity, temporal-credit, optimizer causality, sample efficiency, architecture superiority, lifecycle value, C, Pro, promotion, or retirement claim
```
