# VNFC R02 A0 EM freeze intake

## Decision

```text
object=VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0
evidence_class=A/RECON
result_bearing=false
selected_law=VNFC-R02-ORC-B64-Q52-U64-V1
freeze_complete=true
late_freeze_blockers_closed=4/4
scalar_reverse_graph_closure=complete
bootstrap_source_closure=complete
categorical_reverse_closure=complete
native_dll_dependency_closure=complete
independent_principles_review=CLEAN
science_clean_for_cm_contract=true
implementation_started=false
```

EM selects exactly one finite action law: opaque-rank canonical serialization, a batch-one scalar
CPU binary64 reference, centered scores clipped to `[-16,0]`, exact 52-bit physical probability
apportionment, and exact uint64-midpoint physical CDF sampling.

The same quantized physical probability vector drives stochastic action, forced-command log
probability, entropy, the categorical custom adjoint, gradients, and optimizer input. Deterministic
choice uses the same law's centered `q`; every nonzero `q` difference is strict and exact `q` ties
use opaque rank and null last. Opaque rank never enters a learned tensor.

The exact default ATen scalar callables and their Python/torch/MSVC/UCRT executable bytes are now
prospectively bound in
`VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_KERNEL_BYTE_MANIFEST_20260901.md`. Expected identities and
digests are literals and cannot be regenerated from the checked environment. One fresh interpreter
starts with `-S`, verifies `no_site`, uses no adjacent bytecode, manually appends the exact
site-packages path without `.pth` processing, and performs two identical ordered probes. Through
probe two it requires exact equality to the 942 hashed Python sources in
`VNFC_R02_ORC_B64_Q52_U64_V1_REFERENCE_PYTHON_SOURCE_MANIFEST_20260901.tsv` plus the content-bound
real `scripts/run_vnfc_bpcr_r02_a0.py` `__main__` row, 31 opened distribution resources, and 81
compiled modules, each with a frozen canonical root. The same PID continues
through A0. At probe two the unique resource set must equal all 31 rows and reproduce its literal
4,450-byte root, not merely be a subset. Audit enforcement remains active through publication:
later reads are restricted to the frozen dependency sets or the content-bound R02 source/input
manifest, while writes are separately restricted to declared create-once A0 outputs. Any drift is
`INCOMPLETE`.

Final adapter assembly exposed one additional dependency fact without producing an A0 observation:
the transferred 24-call host path loads the source-keyed BPCR revision-09 native DLL. The byte
manifest now binds the six directly relevant Python/C++/HPP source rows, their canonical root, the
three-native-file domain digest, literal build key
`7222d990642a7e4cb010b6526f17acdb3f3aa85f11d1b8d34be0eedbe11e9c99`, and the exact 213,504-byte
DLL with SHA-256 `dadac9589cf1a885b1acd3891f7411152fa2748cbc34ddbf3537d0b2708f5f68`. The 81-row
module set remains exact through probe two and all source loading. Immediately before the first
formal native adapter call, a frozen load-only same-PID transaction bypasses the loader's build
branch, permits only its existing `ctypes.CDLL` and ABI/magic/size probes, and establishes the exact
82-row post-load set (9,435 canonical bytes, root
`ce22039a3888cea1f3e12963e4e0e3fb8eb00753446b332770cb8257c521ed63`) through publication. It may
not run a compiler/helper subprocess, mutate the cache, derive a new key from the environment, or
fall back. This is dependency completion of the selected law, not a new treatment or result.

The implementation stop exposed one further definition gap: the earlier text promised a fixed
source-owned scalar reverse graph but did not total-order all primitive parent contributions and
shared-leaf accumulation. Closing that gap is a bounded completion of the selected A/RECON law, not
a different mechanism or confirmatory object, so no new Innovator/Pro round is required. The parent
freeze now fixes a memoized scalar DAG, node/edge order, decreasing-node reverse traversal,
decreasing-output-coordinate affine accumulation, explicit add/subtract/multiply/divide/exp/log/
sqrt/sigmoid rules, direct-before-sigmoid SiLU merging, repeated-leaf multiplicity, routing,
mean/max/min/clamp, identity-join ordering, and record/parameter accumulation. It changes no forward
action, probability, RNG, comparator, panel, estimand, budget, or claim ceiling.

Engineering then isolated one bit-reachable bespoke-node omission inside that same reverse graph.
The categorical closure now stores forward `p`, every candidate `log_p`, and entropy `H`; applies
the upstream adjoint after separately rounded log-probability or entropy locals; emits candidate
contributions in ascending opaque-rank/null-last order; and merges them only through the global DAG
accumulator. No reverse probability, log, entropy, or softmax recomputation is allowed.

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

## Independent freeze-closure audit

The independent MARL-principles reviewer previously returned `VERDICT=CLEAN` on the compiled-module
and panel-cardinality repairs. A later engineering review identified the pre-verifier `site` startup
gap. After the `-S`/loaded-source/resource repair was materialized, the same reviewer performed the
required focused recheck and returned `VERDICT=CLEAN`. A third engineering review then required
full 31-row resource equality and continuous audit enforcement through publication; that narrow
repair was materialized, and the same reviewer returned final focused `VERDICT=CLEAN`. No A0
execution, finite-law conformance observation, return, learner effect, or algorithm polarity exists.

After CM stopped on the missing primitive reverse order and then the real `__main__` runner source,
the bounded scalar-DAG and one-row bootstrap-source completions above were reviewed by the same
independent principles route. It returned `VERDICT=CLEAN` and `PRO_REQUIRED=false`: both are
definition completions of the already selected A/RECON law, not a new mechanism or scientific
object.

The same reviewer then audited the stored-value/upstream-adjoint categorical repair and returned
`VERDICT=CLEAN`, `PRO_REQUIRED=false`. The repair closes only bit-exact local reverse semantics; it
does not create an A0 observation or change the forward probability object.

The final focused recheck covered the transferred BPCR DLL/source binding and one-way 81-to-82
same-PID module transition. The same reviewer returned `VERDICT=CLEAN`, `PRO_REQUIRED=false`, and no
repair: the load-only `_compiled_path` substitution preserves the existing cached accessor and ABI
probes while the exact source, path, byte, cache, phase, and continuous set guards exclude a build,
fallback, alternate load, or dependency widening. This remains a bounded dependency completion of
the selected law.

## Frozen evidence purchase

The complete top-level panel contains `304` address rows:

- `288` actual-path rows from 18 descriptors, four presentations, two fresh MAPR fixtures, and
  MAPR/zero-residual DIRECT;
- `4` deterministic source-witness rows; and
- `12` duplicate-tie, nextafter-strict, and fixed/prefix/null primitive rows.

Every primitive top-level row has token addresses zero through three, giving 48 primitive token
records. In `DUPLICATE_TIE` and `NEXTAFTER_STRICT`, tokens one through three are explicitly
null-only variable tokens rather than omitted or inherited records. Exactly one candidate child is
present per support member, including fixed support: the three primitive families contribute
respectively `24/168`, `24/168`, and `32/176` candidate/CDF children, for exact primitive totals of
80 candidate and 512 CDF children.

Every variable-token CDF uses decimal edge indices `0..K`, exact probe strings, and exactly
`5*K+3` records. The nonexistent production word below edge zero and above edge `K` has no
placeholder record. The 36 main model groups and one witness model group define 37 logical steps
per arm, 74 total, but independently evaluate every presentation clone: 288 main plus four witness
optimizer evaluations, for exactly 292 presentation-specific `/REPLAY`, `/GRADIENT`, and
`/OPTIMIZER` records. Primitive groups are forward-law probes only. Predicates remain
address-resolved; no combined `structural` counter is decision authority.

The full law, deterministic witness construction, fixture formulae, address domains, RNG schema,
exact 18-descriptor reconstruction, probability/adjoint/centered-max law, scalar PPO/AdamW step,
containment, pass/fail branches, fresh identities, allowed effects, and owned paths are frozen in
`VNFC_BPCR_R02_FINITE_PHYSICAL_ACTION_LAW_A0_FREEZE_20260901.md`; its referenced byte manifest is
part of the same frozen object.

## Claim ceiling and next action

A complete pass supports only that `VNFC-R02-ORC-B64-Q52-U64-V1` is conformant on the registered
finite panel and is precise enough to justify preparation of one fresh R02 DEBUG. It establishes
no algorithm performance or scientific return polarity.

After this intake is returned to the Direction Manager, CM may implement A0 only. No CM work was
started by this freeze. A valid mismatch returns the law for revision; an incomplete attempt is
repaired and rerun outcome-blind. Neither branch authorizes R01 activity or result-bearing R02 work.
