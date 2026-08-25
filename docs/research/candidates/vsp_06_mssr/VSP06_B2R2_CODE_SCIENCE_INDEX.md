# VSP06-B2R2 Stage-1 code-science index

## Status and boundary

This fresh package implements only the source/config and synthetic structural
proof for `CAND-VSP-06-MSSR@adversarial-revision-v9`. Its strongest permitted
status is `SYNTHETIC_STRUCTURAL_VALID_ONLY`; `formal=false`, `K_search=0`, and
`hypothetical_transitions=0`. The literal provenance anchor for the immediate
predecessor implementation is `7d37be4ff33b2ba4984074383a719390e2cce6b0`;
it is metadata only and is not a runtime locator or read dependency. The package
neither reads the closed predecessor's
artifacts nor contains a fallback locator, cache, receipt, row, catalog, digest,
or runtime-state dependency on that candidate.

Stage 1 supplies no canonical feasibility or infeasibility result. It creates
no canonical catalog, CP-SAT process/model, selector/verifier invocation,
witness, manifest, model load, environment, policy, learner, trainer, optimizer,
evaluator, RNG activity, registered full, result, or readiness output. Root must
later bind a clean final source/config commit, and a new same-direction Explorer
handoff is required before any Stage-2 admission.

## Source responsibilities

| Path | Stage-1 responsibility |
|---|---|
| `vsp06_b2r2_source_bound_symmetry_guaranteed_exact_feasibility.py` | Fixed-order serializer, unchanged split, fresh decision domain, OA recipe, algebraic count, relabeling proof, and synthetic fixed-block first-nonce exercise. |
| `vsp06_b2r2_independent_exact_manifest_verifier.py` | Reconstructs OA, serializer, split, nonce blocks, counts, and decision order without importing the generator; emits only the synthetic verdict. |
| `vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py` | Freezes identities, thresholds, caps, branch precedence, prospective dependency literals, zero counters, and exact fresh/reserved path guards; contains no learning/runtime implementation. |
| `run_vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py` | Read-only `stage1-status` command; runs synthetic proof and reports dependency facts and reserved-path absence without creating paths. |
| `VSP06_B2R2_CONSTRAINT_TARGET_LEDGER_V1.json` | Human-readable frozen Stage-1 scientific and structural literals. |
| `test_vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py` | Proof-sized synthetic/noncanonical invariants and fail-closed guards. |

## Frozen structural construction

The source reconstructs `OA(16,5,4,2)` from GF(4) values encoded as two bits,
XOR addition, and alpha multiplication `[0,2,3,1]`. For fixed `a` then `b`
enumeration, columns are `a`, `b`, `a XOR b`, `a XOR alpha*b`, and
`a XOR (alpha+1)*b`, bound respectively to identity, version, event, decoy,
and reset-Y. Every column has each level four times and every column pair has
all 16 ordered pairs once.

Enumeration order is exactly
`pool -> seed -> panel -> branch -> Y -> replicate -> OA row`. Each cell owns
one disjoint block of 4,096 nonces and emits only the first nonce whose tuple
has its required unchanged split. A missing match is terminal. Bucket override,
salt resampling/substitution, domain extension, and cell-specific conditional
repair fail closed.

The population is proven algebraically, without canonical row enumeration:

| Component | Expression | Rows |
|---|---:|---:|
| Primary | `2 * 4 * 1 * (72+48+12) * 4 * 16` | 67,584 |
| Calibration | `1 * 1 * (32+8) * 4 * 16` | 2,560 |
| Checkpoint | `1 * 4 * 8 * (4+8+2) * 4 * 16` | 28,672 |
| Final KEEP | `1 * 4 * 1 * 1 * 4 * 4 * 16` | 1,024 |
| Total | sum | 99,840 |

The future selected target remains 22,144. Final KEEP retains exactly 64
quartets per seed under the fresh fixed-block domain.

## Serialization and decision order

Tuple serialization is the compact fixed-schema positional JSON array in
declared field order, UTF-8 encoded after requiring all strings to already be
NFC. Duplicate tuple bytes fail closed. Split salt is exactly the eight ASCII
bytes `8100799/`. The fresh decision domain is followed by exactly one real
`0x00` byte. CP-SAT random seed `8100699` is a separate literal. Decision order
uses unsigned SHA-256 digest bytes followed by tuple bytes as the collision
tie-break.

## Result gates and nonclaims

The ledger freezes gate precedence from invalid contract/activity/cap/
provenance through navigation/final-KEEP, selected-P mediation, selected-P
cross-swap, decoy invariance, CURRENT/RESET controls, not-supported, then
supported. It also freezes every threshold and activity cap from the Explorer
handoff. No branch is evaluated in Stage 1.

Stage 1 declares the frozen thresholds and branch labels/order but exposes no
result-classification function and evaluates no branch. The synthetic proof
does not support a selector rank, canonical determinism,
manifest, learner, return, efficiency, arm, access, necessity, mechanism,
general MSSR/MARL, deployment, formal, promotion, or retirement claim. A future
positive result would remain a one-manifest-conditioned finite-budget toy
interpretation and would not establish untouched-generator replication, global
rank, downstream-recipient benefit, or a general MARL mechanism.

## Focused evidence interface

The proof-sized commands are:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B -m pytest -p no:cacheprovider -q tests/experiments/candidates/vsp_06_mssr/test_vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B -m py_compile experiments/candidates/vsp_06_mssr/vsp06_b2r2_source_bound_symmetry_guaranteed_exact_feasibility.py experiments/candidates/vsp_06_mssr/vsp06_b2r2_independent_exact_manifest_verifier.py experiments/candidates/vsp_06_mssr/vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py scripts/run_vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py tests/experiments/candidates/vsp_06_mssr/test_vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B scripts/run_vsp06_b2r2_authenticated_partner_recall_credit_efficiency.py stage1-status
```

The status command reports observed dependency metadata separately from
canonical readiness. An absent or mismatched prospective dependency is not a
Stage-1 proof failure and cannot trigger installation or environment creation.
