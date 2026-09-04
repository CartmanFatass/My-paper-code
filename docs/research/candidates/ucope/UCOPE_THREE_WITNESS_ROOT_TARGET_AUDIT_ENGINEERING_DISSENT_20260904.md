# UCOPE three-witness root-target audit engineering dissent — 2026-09-04

## Disposition

```text
TARGET_PRO_DECISION=ucope-em-convergence-20260904-01
DECISION_AUTHORITY=PRO_FINAL
FINAL_DIRECTION_DECISION=CONTINUE
SELECTED_OBJECT=UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01
ENGINEERING_ACCEPTANCE=BLOCKED_MISSING_RETAINED_INPUTS
SCIENTIFIC_POLARITY=NONE
OBJECT_CARD_FROZEN=false
RESULT_LAUNCH=false
```

The complete Pro decision is valid and final for the question it answered. This dissent names one
missing implementation fact that was not in its GitHub evidence packet: the accepted result did not
retain enough information to compute two of the selected audit's three required observables without
regenerating the environment rows that the Pro decision explicitly fixes at zero.

The direction node must therefore be reopened with this fact. The DM does not replace the selected
object with a retained-only diagnostic, reinterpret the missing values, or relax the zero-new-row
boundary locally.

## Bytes inspected

CM performed a read-only inspection of the sole accepted result summary:

```text
path=temp/directions/ucope/exp/three_witness_hinge_r01_20260904/summary.json
bytes=1273684
sha256=1c8b1d217fc924271da62061f7226642a3d040995aba069cabb5df9ff336b676
policies=6
live_arms_per_policy=2
live_arm_policy_records=12
```

No result was rerun, no generator was invoked, no learner or optimizer was constructed, and no
stored parameter was mutated.

## Direct retained-byte inventory

| Quantity required or relevant | Retained count | Consequence |
| --- | ---: | --- |
| Live learned tail vector `beta_tail` | `12/12` | Available exactly as serialized decimals |
| Live finite-step root vector `beta_root` | `12/12` | The selected audit's third observable is available |
| Live root actions, regret, and `C_root` | `12/12` | Available for the retained finite-step policies |
| Scalar `d_learned_root = ||beta_root - beta_root_target||_inf` | `12/12` | Distance alone does not identify the missing vector or its actions |
| Live-arm induced root-target arrays | `0/12` | First required observable cannot be reconstructed from retained bytes |
| Live-arm exact root-optimum vector `beta_root_target` | `0/12` | Second required observable cannot be evaluated |
| Per-fold root design and target ingredients | `0/6` | Exact solve cannot be recomputed from retained bytes |
| Equivalent sufficient statistics for the live exact solve | `0/6` | No algebraically equivalent retained route exists |
| MSE-exact-reference root vector | `6/6` | Not a substitute: each is induced by a different MSE-exact tail |

The exact missing root-block quantities are `design64`, `probe`, `belief`, `probe_primitive`, and
`tail_return`, or an equivalent sufficient-statistic package that preserves the live FP32 target
construction. None is present in the summary.

## Source-level loss boundary

At the pinned implementation, the result loop computes the relevant values:

```python
targets = CR.root_targets_fp32(blocks["root"], beta_tail)
beta_root_target = CR.exact_solve(blocks["root"]["design64"], targets)
```

but serializes only:

```python
"d_learned_root": float(numpy.abs(root_vector - beta_root_target).max())
```

The `summary` object contains `policies` but no root block, target array,
`beta_root_target`, or sufficient statistic. The accepted result evidence had already bounded the
same scientific limitation: it states that the summary does not evaluate the exact root optimum
induced by each learned tail and therefore cannot separate shifted targets from residual root
optimization.

The six `exact_reference.beta_root` vectors cannot fill the gap. Each solves the root targets
induced by that policy's separately computed MSE-exact tail, whereas the selected audit requires the
target and exact solve induced by each live comparator or treatment learned tail.

## Why exact reconstruction crosses the frozen boundary

`root_targets_fp32` needs row-level beliefs, primitive probe returns, and immediate tail returns;
the live exact solve also needs the root design. Recreating those values from the retained seed,
offset, and source would require calling the deterministic row generator and staging the original
fold rows. The accepted run counted that construction as `983,040` environment episodes and
`4,915,200` environment transitions.

The Pro decision's selected object freezes both counts at zero. Calling the generator would thus
change the selected object's boundary unless the direction node explicitly decides that exact
same-draw deterministic replay is permitted and supplies the corresponding revised evidence class,
question, observable, cost, and claim ceiling. The DM cannot make that direction-tier change.

## Available but non-decisive fallback

A retained-only analyzer could report the twelve finite-step root vectors and the inventory above.
CM directly measured parse-and-extract wall time at `0.1589543 s`; a three-times projection is
`0.476863 s`, below `185.481 s`, with zero environment, RNG, model, optimizer, or mutation work.
That analyzer cannot apply the selected target-versus-fit interpretation map because its first two
observables are missing. Running it as though it answered the Pro question would change the
scientific object and is rejected.

## Required reopened decision

The persistent `em:ucope:convergence` node must decide among at least these direction-tier options:

1. amend the selected A/RECON to permit exact deterministic same-draw row reconstruction and state
   how its zero-new-evidence semantics and claim ceiling change;
2. select a different retained-only object with a question and rule that can be answered by the
   surviving bytes;
3. select the fresh-draw or another prospectively complete discriminator; or
4. park, close, or recast the direction.

Until that response is archived, no successor science card is frozen and no result-bearing
invocation is eligible. The paid-acquisition and COUNT/RAW locks remain unchanged; Portfolio
effects remain reserved.

## Engineering scope

No item from `docs/project/ENGINEERING_SCOPE_SPEC.md` section 4 is needed or added by this dissent.
