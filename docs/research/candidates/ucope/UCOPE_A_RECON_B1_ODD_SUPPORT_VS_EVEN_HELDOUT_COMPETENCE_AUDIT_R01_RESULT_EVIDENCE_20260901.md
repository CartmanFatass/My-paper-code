# UCOPE A/RECON odd-support audit R01 result evidence — 2026-09-01

## Current disposition

```text
LOCAL_STATUS=RETAINED_PENDING_CONVERGENCE
PRO_PACKET_RENDERED=false
PRO_DISPATCH_COUNT=0
DIRECTION_LIFECYCLE_DECISION=NOT_FORMED
```

Root subsequently reported that no explicit audit `go` had been issued and
that Root was in `HOLD` at launch time. The launching EM had inferred execution
authority from the user's prior automatic-progression approval, the parent
assignment to execute after CM/reviewer `CLEAN`, and Root's commit/push of the
exact reviewed implementation. That inference was incorrect relative to Root's
unseen hold state.

Root retains the artifact as usable A/RECON evidence. The coordination error is
material and remains recorded, but it did not change the frozen object, source,
input, resource admission, execution count, or interpretation boundary: the
run used the exact independently reviewed commit, passed a fresh prospective
4 GiB admission, executed once outcome-blind, published one create-once artifact,
and performed no training, selection, acquisition, tuning, retry, or COUNT/RAW
work. No additional result values were read after the hold message.

## Exact launch facts

The launcher was native subagent:

```text
/root/dm_sh_ucope_wave1/em_smx_ucope_convergence
```

The reviewed implementation was fixed at Git commit
`5ac4165cc051e41c298f76b96a835a696f360b88` on `main` and `origin/main`.
Its frozen files matched the reviewer-approved SHA-256 values:

```text
support_audit.py  20fac6a4bb16b2749d6d4bbd9a164e4303ea5e79faf6ee1691ee00b9938fd6bd
CLI               35a83c53fabc713b8ff3cb5d7d32345e0bb73f8122f59ccde8bce19fbe44c364
tests             a80e98eb987b572803dc4b1fcf4d884f5f1d0800bc81b8133b63328cf1ca0828
```

Immediately before launch, the central resource command was:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/hmasd_resource_preflight.py admit-memory --out 'temp/directions/ucope/recon/ucope-scout-r01-b1-odd-support-audit-20260901-01-admit-memory.json'
```

The receipt records capture `2026-09-01T17:51:01.537305Z`, assessment
`2026-09-01T17:51:01.563700Z`, physical and effective availability both
`15,831,928,832` bytes, and both 4 GiB floors passing.

The sole audit command was:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_ucope_b1_odd_support_audit_r01.py --complete-root 'temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-04/execution/complete' --admission-receipt 'temp/directions/ucope/recon/ucope-scout-r01-b1-odd-support-audit-20260901-01-admit-memory.json' --output 'temp/directions/ucope/recon/ucope-scout-r01-b1-odd-support-audit-20260901-01/odd-support-audit.json'
```

It exited `0` after approximately `18.52 s`. No retry was launched.

## Artifact facts already observed

The create-once output is:

```text
temp/directions/ucope/recon/ucope-scout-r01-b1-odd-support-audit-20260901-01/odd-support-audit.json
size     2,218,087 bytes
SHA-256  0d52ba383f156167be805612180ecd44517bdf1d65fa389f87e1638c9655b1de
```

Before Root's hold message, the final validator accepted the artifact against
the frozen binding. Already-read mechanical observations were: 72 odd rows,
72 recomputed even rows, 72 exact even-parity matches, pre-tail wall
`12.437480400010827 s`, peak RSS `210,489,344` bytes, scratch peak `0`, and
durable output `2,218,087` bytes.

The already-completed independent recomputation found:

- all 72 odd-support policies finite and unique;
- zero odd-competent and zero odd-near policies; every arm had zero of three
  qualifying final seeds;
- final paired `FT-XF-FLEX : FT-XF-BC` dominance counts of `2:3`, `2:2`,
  `4:1`, and `3:2` at updates `40`, `80`, `160`, and `320`; only update 160
  was clear, so there was no adjacent learning-curve separation;
- all six final paired `MT-XF-FLEX` and `FT-XF-FLEX` tail maps equal and all
  six root-vector distances zero, hence no MT/FT root separation;
- across-arm similarity true only at update 40 and false at 80, 160, and 320;
  therefore `all_similar_odd_failure=false`; and
- all routing predicates false except `oracle_unique=true`, yielding
  `MAP_NOT_UNIQUE_NEW_CONVERGENCE_REQUIRED`.

These are recorded observations, not an adopted direction conclusion. The
existing Pro map does not uniquely assign this pattern to continue, park,
close, or recast. No paid-acquisition evaluation occurred and COUNT/RAW remain
locked.

## Limitations and next authority boundary

The artifact is retained, but no additional value may be read in this usage-stop
turn. Its uncovered route requires a new persistent `em:ucope:convergence` round
before any direction recommendation. No local lifecycle action is inferred.
