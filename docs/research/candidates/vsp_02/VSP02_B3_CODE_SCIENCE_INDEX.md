# VSP02-B3 code-science index

This is the source/config candidate for the frozen ordinary-B discriminator
`VSP02-B3-LIFECYCLE-CREDIT-SIGN-BRIDGE`. It contains no registered-full result
and makes no technical-acceptance or scientific-success claim. CPM retains
review, runtime admission, the sole registered full, publication, readiness,
and technical acceptance; Explorer retains scientific intake and successor
choice.

```text
treatment=VSP02-B3-LIFECYCLE-CREDIT-SIGN-BRIDGE
candidate=CAND-VSP-02@adversarial-revision-v8
source=experiments/candidates/vsp_02/vsp02_b3_lifecycle_credit_sign_bridge.py
runner=scripts/run_vsp02_b3_lifecycle_credit_sign_bridge.py
tests=tests/experiments/candidates/vsp_02/test_vsp02_b3_lifecycle_credit_sign_bridge.py
index=docs/research/candidates/vsp_02/VSP02_B3_CODE_SCIENCE_INDEX.md
public_result=docs/research/candidates/vsp_02/VSP02_B3_LIFECYCLE_CREDIT_SIGN_BRIDGE_RESULT.json
public_result_status=ABSENT_UNTIL_ACCEPTED_REGISTERED_FULL
host=VSP02-A2-PHYSICAL-LIFECYCLE-HOST-v1
accepted_b2_source=bd0da64f851718cf0b5d59b144d99a7006ff2a73
accepted_b2_publication=51aa863367b2f0f25ff6bf3606623496daca8d73
implementation_base=26b8a800c8d2dd9bce60c3452d1dae637b58e1f3
resource_class=B_TOY_LIGHT
formal=false
evidence_search=H=4|K_search=0|hypothetical_transitions=0
arms=RL_ORIGINAL|CREDIT_SIGN_BRIDGE
training=5 fresh units|128 updates/unit/arm|8 real original-generated episodes/update|4/4 cue balance
evaluation=128 common held-out episodes/arm/unit|64/64 cue balance|10 final checkpoints
planned_activity=5120 training episodes|1280 optimizer updates|1280 evaluation episodes
hard_caps=145348 transitions|30 CPU minutes|2 GiB|one registered full
retry_rescue_sweep_extra_arm_seed_checkpoint=0
implementation_status=SOURCE_CANDIDATE_PENDING_CPM_REVIEW
```

## Frozen treatment binding

- The only training host/action generator is `RL_ORIGINAL`. Each update freezes
  eight canonical JSON rows before either learner update. Both arms use the
  same seeded minibatch permutation, and bridge computation is surrounded by
  original model, Adam, action-RNG, successor-state, and batch hashes.
- Each unit constructs one float64 `GRUCell(10,16)` actor/critic model and one
  empty Adam state, then deep-clones both byte-identically into exactly two
  arms. The five root identities are `VSP02-B3-U01..U05` with decimal roots
  `22030001..22030005`; the SHA-256 stream namespace is disjoint from B1V2 and
  B2.
- For every lifecycle row the bridge first computes its own forward state,
  baseline, return, and `A=G-b`. Only then does it read the frozen cue and form
  `c`, where cue 0/HOLD and cue 1/RELEASE are positive and the other actions
  are negative. The sole intervention is
  `c*detach(abs(A))` in the sampled-action log-probability term. Entropy,
  critic, masks, optimizer, global clip, shared backbone, and evaluation remain
  on the B2 host route.
- Missing `G`, a missing/masked lifecycle advantage, or any nonfinite return,
  advantage, coefficient, loss, gradient, or pre-clip norm raises before the
  registered artifact can validate. `A=0` gives exactly zero actor coefficient;
  no epsilon, imputation, normalization, or rescaling exists.
- The oracle helper is absent from collection and evaluation and is never
  called by the original loss route. It is accessed after the bridge forward
  pass and enters only the scalar actor coefficient.

## Artifact and lifecycle binding

The manifest freezes source revision, run identity, two-arm/root/RNG contracts,
loss routes, exact planned activity, caps, and zero retry/rescue/sweep. The
runner requires a source revision equal to `HEAD`; all four claim paths plus
the B2, B1V2, and direct A1 host dependencies tracked and clean at that `HEAD`;
the exact worktree-local canonical run root
`temp/sessions/code_project_manager/vsp02_b3_lifecycle_credit_sign_bridge/`;
the canonical manifest location; and the bound worktree CWD. A sibling,
nested, or merely marker-containing root is rejected before claim creation or
runtime. The runner atomically creates an exclusive claim before the unique
`run_treatment` call and writes both manifest/result artifacts once. There is
no retry or corrected-full path.

Retained validation is pure: it checks manifest/preflight/result identities,
write-time evidence digests, unit/arm/update counts, route literals, advantage
and magnitude records, original-generator noninterference receipts, activity,
caps, and source binding without invoking a host, model, Adam, optimizer step,
trainer, evaluator, or the treatment. Hashes are mutation detectors and do not
substitute for the retained real-host rows and update/evaluation records.

## Result and interpretation boundary

The public result JSON is deliberately not created by implementation. Only an
accepted sole registered full may populate it. The result schema has exactly
the three frozen branches: `B3_SIGN_BRIDGE_LOCAL_SUFFICIENCY`,
`B3_SIGN_ONLY_INSUFFICIENT`, and `B3_INCONCLUSIVE_OR_INVALID`. Construction,
contract, activity, or other validity failures represented in a B3 result map
to `B3_INCONCLUSIVE_OR_INVALID`; there is no fourth scientific result branch.
A future result remains local to the
realized bridge `|A|`, privileged correctness sign, and off-policy shadow
coverage. It cannot establish general actor-critic, baseline, recurrent,
optimizer, temporal-credit, architecture, or lifecycle value claims, and it
cannot choose C, promotion, retirement, retry, rescue, or a successor.
