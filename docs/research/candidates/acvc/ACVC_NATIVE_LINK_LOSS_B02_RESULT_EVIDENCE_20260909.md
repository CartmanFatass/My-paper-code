# ACVC-NATIVE-LINK-LOSS-B02 — P79 technical evidence

## Engineering acceptance

Identity adaptation accepted; no P79 scientific invocation yet. Contract:
[B02 card §§1–5](ACVC_NATIVE_LINK_LOSS_B02_SCIENCE_CARD_20260909.md) and
[P79 prospective facts](ACVC_NATIVE_LINK_LOSS_B02_P79_PROSPECTIVE_FACTS_20260909.json)
at `56ce830386cfab6be30b217e5cc5b0d0f8109120`. The designated `codex/acvc` checkout
`C:/Projects/HMASD-worktrees/codex-acvc` began clean at that revision. Shared native,
UCOPE/MGTAP, fixed checkpoint, DM-owned inputs and all P78 evidence remain unchanged.

The sole source adaptation adds seed8902 to the existing runner CLI, publishes the
corresponding B02/P79 identity, and uses a dedicated `launch_b02.sh` with the new run root
and admission path. `binding.py`, `model.py`, `learner.py`, `report.py`, PPO, initialization
laws, recurrence and sampling are unchanged from accepted P78 source `f42902116`.
The new master flows through those already-parameterized private streams. P78 gate
checkpoints are never loaded. The source reference and retained P78 bytes remain recoverable
at their original revisions; there is no compatibility shim or generic registry.

Scope §4 additions: **none**, as required by B02 card §5. Source change is 20 added /
5 removed non-test lines, including the dedicated14-line launch command. The reused
attempt now has484 non-test lines and the runner150 lines, within2000/600 limits.

## Focused checks and reused review

Reuse the accepted P78 independent semantic review and unchanged information/identity,
recurrent replay, credit/masking, common-initialization/containment and primary-output
coverage documented in [P78 evidence](ACVC_NATIVE_LINK_LOSS_B01_RESULT_EVIDENCE_20260909.md).
No second semantic implementation or full-suite repetition is needed for this identity change.

Current synthetic invocation, local scientific Python:

```text
python -m pytest -q -p no:cacheprovider --basetemp <new owned P79 temporary directory>/pytest
  tests/experiments/candidates/acvc/native_link_loss_b01/test_link_loss.py::test_primary_rules_and_complete_synthetic_publication[8902]
  tests/experiments/candidates/acvc/native_link_loss_b01/test_link_loss.py::test_b02_stream_identity
```

Result: **2 passed**, pytest4.16 s; complete command wall **5.4396806 s**, charged to the
logical study and both learned arms. The Python wrapper reported5.234 s internally and
confirmed its new `temp/directions/acvc/test/p79_identity_*` directory was absent after
standard temporary-directory teardown. There was no native environment or scientific
training/evaluation exposure. The old P78 blocked scratch path was neither touched nor retried.

Checks cover B02 object/allocation/master publication, CLI propagation, fresh reset identities
in every synthetic phase, checkpoint master fields, all-arm post-learner output publication,
2240 distinct action streams shifted exactly100000 from P78, separation from all initialization/
reset streams (2789 distinct declared values total), and the dedicated P79 launch identity.
The synthetic fixture is not scientific performance evidence. Complete native output and
actual process-exit accounting remain to be established by the sole allocated invocation.

## Prospective cost and publication coverage

The complete work law is unchanged: T/G each512×256 collection steps,1024 Adam updates
with chunk32 recurrent replay and32×256 final steps; C/F each32×256 final steps. Together:
294912 team steps,2048 Adam calls,512 rollouts,1152 scored resets and4 unscored constructor
resets. G retains its additional recurrent residual cost. Required checks, imports/startup,
C/F evaluation and publication/exit are charged to both learned arms; the other learned
fit is excluded from an arm's bill. No native pilot or alternative configuration is added.

P78 same-count costs are the measured reference (work multiplier1): process359.17 s,
T199.8208294 s, G215.5117409 s, whole373.4069735 s including14.2369735 s checks. Substituting
the current5.4396806 s check cost while retaining P78 scientific-path costs gives a planning
projection of **T191.0235365 s, G206.7144480 s, whole364.6096806 s**. New initialization,
trajectory and machine contention remain unknown; this is a reuse-based projection, not
a timing observation of P79. Caps remain1800 s per complete arm and3600 s complete study.

Post-learner coverage uses the same synthetic publication path as the actual runner,
with new identity/reset/checkpoint fields read back. All training/final native S/J outcomes,
gate choices, update records and five fixed paired contrasts will be retained separately
from P78. Conditional SE uses32 paired joint episodes; no selected-max SE or pooling with
P78's evaluation episodes is introduced. Final T/G checkpoints are the only learned outputs.

## Execution boundary

One accepted scientific invocation is allocated, with master8902 and the unchanged frozen
DENSE input digest `f648f2b100d07335ccd9c79c0476b8e9dba0c1644ae837d622b0c5f711030790`.
Route: configured `wsl_4070`, CPU/FP32, Torch intra/inter-op1, unchanged native NumPy;
detached exact-source worktree and configured `agent-task`. Fresh actual-node admission
is joined by `&&` to the committed B02 launch command. Runtime root:
`temp/directions/acvc/exp/native_link_loss_b02_8902_p79_20260909/`.
No dependency on the old P78 remote worktree, local fallback, scientific retry, resume,
extra evaluation, tuning or second new instance is allocated. CM is sole observer through
terminal collection and technical acceptance; DM owns all-outcome scientific intake.
