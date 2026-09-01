# VNFC R02 A0 EM freeze intake

## Decision

```text
object=VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0
evidence_class=A/RECON
result_bearing=false
selected_law=VNFC-R02-ORC-B64-Q52-U64-V1
freeze_complete=true
implementation_started=false
```

EM selects exactly one finite action law: opaque-rank canonical serialization, a batch-one scalar
CPU binary64 reference, centered scores clipped to `[-16,0]`, exact 52-bit physical probability
apportionment, and exact uint64-midpoint physical CDF sampling.

The same quantized physical probability vector drives stochastic action, forced-command log
probability, entropy, the categorical custom adjoint, gradients, and optimizer input. Deterministic
choice uses the same law's centered `q`; every nonzero `q` difference is strict and exact `q` ties
use opaque rank and null last. Opaque rank never enters a learned tensor.

## Why this law

Canonicalization before numeric execution removes the presentation-dependent `F.linear`/pooling
surface exposed by R01. The 52-bit apportionment makes every physical probability positive,
binary64-exact, and exactly normalized. Integer CDF comparison removes floating boundary ambiguity.
The batch-one serial oracle prevents row position, vector lane, batch companion, or reduction order
from silently becoming an identity channel. A custom zero-residual identity join preserves DIRECT
containment while leaving its residual output learnable.

This is new R02 treatment semantics, not an R01 repair. Its declared limitation is conditioning on
one treatment-blind episode-level opaque total order and one frozen host/kernel identity.

## Direct scientific inputs

- the complete Pro decision `CLOSE_AND_REVISE_R01`, response SHA-256
  `7b4938a9150f66ae6428b90dba14a1a70d2e53e071a8de4c262e041a0c885f16`;
- the exact source-only N=5/reverse witness construction at commit
  `98c96af0fdf66f4f539e841218a1de175dfa9db7`;
- committed public MAPR/DIRECT shapes, serialization-only opaque-rank contract, exact mean, training
  path, and finite action source; and
- the project A/RECON incomplete-attempt and bounded-claim semantics.

No R01 runtime, native trace, quarantine, endpoint, checkpoint, optimizer tensor, or RNG artifact
was read or transferred. Independent reasoning routes were search coverage only, not empirical
replication or decision authority.

## Frozen evidence purchase

The complete top-level panel contains `304` address rows:

- `288` actual-path rows from 18 descriptors, four presentations, two fresh MAPR fixtures, and
  MAPR/zero-residual DIRECT;
- `4` deterministic source-witness rows; and
- `12` duplicate-tie, nextafter-strict, and fixed/prefix/null primitive rows.

Every variable-token CDF boundary, exact boundary, adjacent binary64 value, and adjacent production
word is exhaustively probed. The 36 main model groups and one witness model group perform one
forced replay and one source-only synthetic optimizer step in each arm: 37 steps per arm, 74
total. Primitive groups are forward-law probes only. Predicates remain address-resolved; no
combined `structural` counter is decision authority.

The full law, deterministic witness construction, fixture formulae, address domains, RNG schema,
exact 18-descriptor reconstruction, probability/adjoint/centered-max law, scalar PPO/AdamW step,
containment, pass/fail branches, fresh identities, allowed effects, and owned paths are frozen in
`VNFC_BPCR_R02_FINITE_PHYSICAL_ACTION_LAW_A0_FREEZE_20260901.md`.

## Claim ceiling and next action

A complete pass supports only that `VNFC-R02-ORC-B64-Q52-U64-V1` is conformant on the registered
finite panel and is precise enough to justify preparation of one fresh R02 DEBUG. It establishes
no algorithm performance or scientific return polarity.

After this intake is returned to the Direction Manager, CM may implement A0 only. No CM work was
started by this freeze. A valid mismatch returns the law for revision; an incomplete attempt is
repaired and rerun outcome-blind. Neither branch authorizes R01 activity or result-bearing R02 work.
