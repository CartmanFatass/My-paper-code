# CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2 prelaunch acceptance

Date: 2026-07-23

```text
implementation_base_commit=0aeccfc444b514bb2ed405163c940b0242384137
artifact=logs/nonformal_cross_lifecycle_handoff_g2_trainable_20260723_pm2
formal=false
exercise_result=SOURCE_NON_IDENTIFIABLE_HANDOFF_G2
focused_tests=15_passed
iteration_cost=0
iterations_remaining=3
```

## Accepted implementation

The active G2 line now contains:

- counter-based train/IID/held-out anonymous handoff ledgers;
- exact six-field actor and ten-field critic separation;
- matched TEAM_REC/DUM/EHC module inventories;
- per-member and team recurrence with explicit lifecycle ownership;
- CREATE mark sampling and held `base_logits + W_z(m*z)` treatment;
- stored-draw joint replay, GAE, four-pass PPO and CPU checkpoint/resume;
- train/evaluate/analyze/exercise runner with paired bootstrap and the frozen
  nine-branch selector.

The closed G1 environment, model, runner and their tests were deleted in the
same active-line boundary. G1 design, evidence, formal artifacts and Git history
remain the authoritative archive; no compatibility reader or alias was added.

## Proof-sized acceptance

Focused CPU one-thread suite:

```text
tests/ha_ctse_process_cross_lifecycle_handoff_g2_test.py
tests/ha_ctse_process_ehc_handoff_g2_test.py
tests/run_cross_lifecycle_handoff_g2_test.py
15 passed
```

The fresh reduced exercise produced three final checkpoints, 12 evaluation
cells, source controls and eight exact post-creator-departure snapshot audits.
It recorded four optimizer steps and four completed episodes per arm, no rolling
or temporary residue, and `operational_errors=[]`.

The analyzer selected `SOURCE_NON_IDENTIFIABLE_HANDOFF_G2` only because the
exercise has eight audit episodes rather than the frozen formal quota of 128 per
replicate. This is the registered nonformal behavior. The formal validator
rejected the artifact because `formal=true` is absent.

Additional focused evidence covers exact logit links, matched initialization,
replay equality, treatment-gradient fences, checkpoint source identity, final
same-command resume, evaluation tamper rejection, selector precedence, formal
token rejection and bounded retry of transient OneDrive atomic-replace locks.

## Protected-semantics inspection

- Target bit is absent from successor actor traces and present only in critic
  fields after CREATE.
- Creator member state is deleted at terminal LEAVE; successor JOIN initializes
  exact zero even on physical-slot reuse.
- TEAM_REC and held state survive outside slot ownership and reset only at
  episode start.
- Mark intervention branches from one exact snapshot after creator departure;
  only held mark changes under common future source state.
- Primitive/mark probabilities, RNG generators, old log probabilities,
  checkpoint counters and optimizer exposure are serialized and fail closed.
- CPU-only execution performs no device transfer or backend fallback. Evaluation
  is deliberately small serial CPU work; no accelerator synchronization exists.
- External reward is successor correctness only; no intrinsic reward, shaping,
  identity cue, G0/G1 import or changed result threshold exists.

## Formal launch boundary

After this exact package is committed and pushed, resolve that integrated commit
and one fresh run root. The registered experiment operator receives the frozen
CPU one-thread commands:

```text
train --formal --authorization-token AUTHORIZE_CROSS_LIFECYCLE_COMMITMENT_HANDOFF_G2_FORMAL_CPU_V1
evaluate --formal
analyze --formal
```

The operator remains silent and returns once at COMPLETE or ERROR. A valid
formal result consumes conclusion-bearing iteration 3; three iterations remain
until then.
