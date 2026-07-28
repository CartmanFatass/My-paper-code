# D7.S audit run 2 — disposition of a valid non-affirmative result

The first formal D7.S event-aligned source audit has run to completion. It is
mechanically clean and its result is non-affirmative. This round asks for **one
scientific decision: how this run is dispositioned under the frozen R3 contract,
and what evidence action that disposition implies.**

Four asks follow, tree-structured, because the later ones depend on the first.

**Discarding this framing is a legitimate answer.** If the right reading of this
run is not one of the two the question sets up, say so and say what it is. Every
measured number below is offered as a claim to falsify against source and
artifact, not as a premise to accept — the recomputations are described precisely
enough to be repeated.

---

## Frozen inputs — not review surface

These are settled and are not being reopened:

- The R3 contract itself: estimand, event definition, horizons, controllers,
  normalizers, thresholds, the eight topology seeds, episode counts, the
  bootstrap procedure, `stream_seed` semantics, and the ten branch semantics.
- The run is complete and will not be re-executed to change these numbers.
- The instrument defects named below are the Project Manager's to repair, and
  the repairs are already scheduled. **What is asked here is the scientific
  disposition of the result, not the code fix.**

## The run

```text
run          = GitHub Actions 30289161086, tag d7s-audit-2
stage_commit = 1b17dfb0            (the run's own commit; this round's fence
                                    commit is later and adds only this question)
contract     = D7_S_EVENT_ALIGNED_SOURCE_AUDIT, procedure d7s_event_aligned_v1
shards       = 8/8 success, one wave, no timeout, no killed shard
```

Mechanical validation, all from the pooled artifact: `smoke=False`,
`conformance.ok=True`, invalidated pairs 0, `topology_hash_ok=True` with zero
failures, `arm_distinct_ok=True`, `support.ok=True` at 8/8 calibration and 8/8
audit topologies, `all_seed_controlled=True`, topology seeds exactly the frozen
`20260726`–`20260733`.

`all_seed_controlled=True` is the R3 §E provenance the prior Stage B ruling
found missing, so this run's contrasts are matched evidence in a way ep64's were
not.

## Repository fact — verified by reading source at the fence commit

1. **`decide_branch`** (`scripts/audit_d7_s_event_aligned.py:1046-1075`)
   implements the ten registered branches by first-match precedence. Branch 3 is
   `if primary_g_degenerate_flag: return "PRIMARY_G_DEGENERATE"`.

2. **The flag is a hardcoded literal.** `assemble_audit_result` calls
   `decide_branch(..., primary_g_degenerate_flag=False, ...)` at `:3788`. The
   function that would compute it, `primary_g_degenerate` (`:750-755`), is
   **never called anywhere in the file**. Its only occurrences are its own
   definition, the parameter name at `:1047`, and the read at `:1055`. Branch 3
   is therefore structurally unreachable for every input.

3. **The registered meaning of branch 3.** R2 §7, carried forward verbatim by
   R3: *"Emit `PRIMARY_G_DEGENERATE` and stop before margin interpretation when
   all four component sequences are exactly arm-invariant under pairing, or
   `B_m` cannot establish a positive source-control contrast."* R2 §10 glosses
   branch 3 as *"primary safety objective cannot separate source controls"*.

4. **The gate's own `B_m` requirement.** R2 §8: `T_stable = U*_stable +
   0.10·B_stable`, stable clears iff `UCB95(T_stable) < 0`; `T_flex = U*_flex −
   0.10·B_flex`, flex clears iff `LCB95(T_flex) > 0`; and *"each limb
   additionally requires `LCB95(B_m) > 0`"*.

5. **The one permissible expansion.** R2 §9: *"only when conformance and support
   pass, `B_m` points are positive, the relevant `T_m` points have intended
   signs, and one or more required bounds remain unresolved — add exactly the
   eight topologies 20260734–20260741 ... **No second expansion.** Never expand
   on a wrong-direction point, a resolved-negative branch, `B_m ≤ 0`, support
   failure, or conformance failure."*

## Measured — recorded, and recomputed from the artifact

Recorded in the pooled artifact:

```text
b_stable_lcb   -0.077367      t_stable_ucb   +7.206993      t_stable_lcb   -2.189143
b_flex_lcb     -8.648833      t_flex_lcb    -14.293054      t_flex_ucb     +3.115871
recorded branch = SOURCE_NECESSITY_UNRESOLVED       part_a = NOT_APPLICABLE
```

No affirmative branch could fire: `stable_clears`, `flex_clears`,
`flex_affirmative_miss` and `stable_affirmative_miss` (`:1060-1063`) each require
a strictly positive `b_*_lcb`, and both are negative.

**Point estimates are not recorded by the instrument at all** — only the six
bounds above are written to the artifact. The Project Manager recomputed them
from `topology_units` in the pooled JSON, using the instrument's own
`hierarchical_bootstrap_events(..., compute_point=True)` per topology and equal
topology weighting. The point path uses the true argmax and consumes no RNG, so
it is seed-independent.

**Verification of that recomputation:** feeding the same `topology_units` back
through the instrument's own `compute_t_m_bootstrap` at the registered
`BOOTSTRAP_ITERS`/`BOOTSTRAP_SEED` reproduces **all six recorded bounds to
better than 1e-12** — `b_stable_lcb` recomputed `-0.077366986884` against
recorded `-0.077366986884`, and likewise for the other five. That is what
establishes the unit→quantity mapping used for the points below is the same one
the run used.

```text
quantity                        point        recorded bound
B_stable  (calibration stable)  +0.180139    LCB95 = -0.077367
B_flex    (calibration flex)    +4.288854    LCB95 = -8.648833
U*_stable (audit stable)        +1.254074    —
U*_flex   (audit flex)          -4.122402    —

T_stable point = U*_stable + 0.10·B_stable = +1.272088   (intended sign: negative)
T_flex   point = U*_flex   − 0.10·B_flex   = -4.551287   (intended sign: positive)
```

Per-topology spread is wide on every quantity: `B_flex` ranges `-17.15` to
`+19.03` across the eight topologies, `U*_flex` `-30.07` to `+7.40`.

## Project Manager inference — marked as inference throughout

None of this is repository fact or an external ruling.

**(a) The natural reading of the missing flag.** `b_m_positive_lcb` has **no
production derivation**, because the function that would consume it is never
called. Reading it from the recorded bounds gives:

```text
b_stable_lcb > 0                                False
b_flex_lcb   > 0                                False
primary_g_degenerate(arm_invariant=False,
                     b_m_positive_lcb=False)    True
```

Both limbs fail `LCB95(B_m) > 0` by the contract's own §8 requirement, so
under the natural reading this run is branch 3.

**(b) Why the reading is not obviously arbitrary.** The registered estimand is a
**ratio**, `U*_stable,src / B_H ≤ -0.10` and `U*_flex,src / B_H ≥ +0.10`, while
the implemented gate is the **linear** form `T_m`. Those two are equivalent only
when `B_m > 0`; at `B_m ≤ 0` the division reverses the inequality. That appears
to be exactly why §8 carries `LCB95(B_m) > 0` as a separate requirement, and why
§7 names a non-positive `B_m` as degeneracy rather than as a small effect. This
is the Project Manager's reconstruction of the contract's intent, not a quoted
ruling.

**(c) An ambiguity the wiring cannot avoid.** §7 says "`B_m`" without a limb
qualifier, but §8 states the requirement per limb, and there are two `B_m`
quantities. So `b_m_positive_lcb` could be conjunctive (`b_stable_lcb > 0 and
b_flex_lcb > 0` — degenerate if either limb fails) or disjunctive (degenerate
only if both fail). **On this run both limbs are negative, so both readings give
`True` and the disposition of this particular run does not depend on resolving
it.** The wiring does.

**(d) A correction to the Project Manager's own earlier framing.** The internal
evidence note recorded that the two labels point at opposite next experiments —
`SOURCE_NECESSITY_UNRESOLVED` inviting more replicates and topologies,
`PRIMARY_G_DEGENERATE` saying more replicates would be a power rescue of a
degenerate design. **On the measured numbers that opposition appears to be
false.** §9 permits expansion only when the relevant `T_m` points have intended
signs; both `T_m` points have the **wrong** sign (`T_stable` is `+1.27` where it
must be negative, `T_flex` is `-4.55` where it must be positive), and §9 says
never to expand on a wrong-direction point. So §9 appears to forbid the
expansion **independently of which label is correct**. Note this cuts against the
framing the question would otherwise have rested on, which is why it is stated
here rather than left out.

Also note §9's expansion predicate keys on `B_m` **points**, which are both
**positive** here (`+0.18`, `+4.29`) — it is the `T_m` points, not `B_m`, that
fail. And `expansion_allowed` (`:1095`) is itself dead code, never called from
`main()`; expansion currently happens by a human passing `--topology-seeds`, so
no code enforces §9 either way.

## What is asked

**Q1 — the disposition.** Under the frozen contract, is run 30289161086's
registered branch `PRIMARY_G_DEGENERATE` rather than the recorded
`SOURCE_NECESSITY_UNRESOLVED`? A hardcoded literal prevented the instrument from
evaluating branch 3 at all; the question is what the contract says the answer
is, given the recorded bounds. If neither label is right, name the correct one.

**Q2 — the wiring, conditional on Q1.** For `primary_g_degenerate` to be wired
so this cannot recur, `b_m_positive_lcb` needs a definition across the two
limbs. Conjunctive or disjunctive, per (c)? This changes a result branch, which
is why it is asked rather than decided locally.

**Q3 — expansion.** Is the Project Manager's reading in (d) correct — that §9
forbids the one permissible expansion here on the wrong-direction `T_m` points,
independent of Q1? If it is wrong, say where.

**Q4 — the smallest unit, and the next action.** What does this run retire or
support, at the smallest unit it actually settles? And what is the next evidence
action: repair the primary-`G` construction or the instrument, revise the
estimand or its normalizer, accept a negative result on source necessity, or
something else? If `B_m` genuinely cannot be established positive on this
environment, that bears on whether the D7.S proposition is measurable as framed.

## Required response sections

```text
1. VERDICT_Q1     branch label, with the contract clause it follows from
2. VERDICT_Q2     b_m_positive_lcb definition, or an explicit scope-out
3. VERDICT_Q3     expansion admissible or not, and why
4. SMALLEST_UNIT  what this run retires or supports
5. NEXT_ACTION    the single next evidence action, and what it would decide
6. CHALLENGES     which claims above you checked and found wrong
```

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R3.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md`
- `scripts/audit_d7_s_event_aligned.py`
- `logs/d7s_audit_2_30289161086/pooled/d7_s_event_aligned.json`
- `docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_AUDIT_2_RESULT_AND_A_MISLABELLED_BRANCH.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_A_RESULT_BRANCH_THAT_CANNOT_FIRE.md`
