# Step E — every registered R4 outcome, from a real dev-topology unit

R4 closure step E: the proof-sized assembled-path exercise on development
topology `20260725` only. **Not a result, and structurally cannot become one** —
it reads a `SMOKE_NOT_A_RESULT` artifact and fabricates limb values.

```text
smoke run    logs/d7s_r4_step_e_20260728_095707, --smoke, topology 20260725
             branch SOURCE_EVENT_SUPPORT_INSUFFICIENT, r4_contract None
exercise     scripts/d7s_r4_assembled_path_exercise.py
outcomes     13 distinct -- all nine combined results, all four precedence branches
verdict      STEP_E_ASSEMBLED_PATH_OK
```

## What this adds over the reachability check already done

The realization-conformance review drove all fifteen limb-state combinations
through the real `assemble_audit_result` using **hand-built** topology results.
That proves the assembler maps states to branches. It does not prove that the
shape a **real environment run** emits — carried through serialization and the
pooler's reconstruction — feeds those branches at all.

This exercise starts from the artifact of a real smoke run and rebuilds its
topology unit with the pooler's own `_reconstruct_topology_result`: the
production path, not a fixture.

## The nine combined results

```text
MATERIAL / MATERIAL                  PERSISTENCE_NECESSARY_SOURCE
MATERIAL / AFFIRMATIVE_NONMATERIAL   STABLE_PERSISTENCE_WITHOUT_MATERIAL_FLEX_RENEWAL
MATERIAL / UNRESOLVED                MATERIAL_STABLE_PERSISTENCE_IDENTIFIED
AFFIRMATIVE_NONMATERIAL / MATERIAL   FLEX_RENEWAL_WITHOUT_MATERIAL_STABLE_PERSISTENCE
AFF_NONMAT / AFF_NONMAT              NO_MATERIAL_SOURCE_NECESSITY_IDENTIFIED
AFF_NONMAT / UNRESOLVED              NO_MATERIAL_STABLE_PERSISTENCE_IDENTIFIED
UNRESOLVED / MATERIAL                MATERIAL_FLEX_RENEWAL_IDENTIFIED
UNRESOLVED / AFF_NONMAT              NO_MATERIAL_FLEX_RENEWAL_IDENTIFIED
UNRESOLVED / UNRESOLVED              SOURCE_NECESSITY_UNRESOLVED
COMPONENT_INVARIANT / MATERIAL       FLEX_RENEWAL_WITHOUT_MATERIAL_STABLE_PERSISTENCE
MATERIAL / COMPONENT_INVARIANT       STABLE_PERSISTENCE_WITHOUT_MATERIAL_FLEX_RENEWAL
```

**Both flex-only positives are present**, which is what Pro named specifically:
`MATERIAL_FLEX_RENEWAL_IDENTIFIED` from `(UNRESOLVED, MATERIAL)`, and
`FLEX_RENEWAL_WITHOUT_MATERIAL_STABLE_PERSISTENCE` from **both**
`(AFFIRMATIVE_NONMATERIAL, MATERIAL)` and `(COMPONENT_INVARIANT, MATERIAL)`. The
gap R3 had — a valid flex positive hidden under a stable-negative branch — is
closed and demonstrated rather than asserted.

## The four precedence branches, and the two frozen reason codes

```text
component audit missing   INVALID_EVENT_ALIGNED_AUDIT
                          [MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING]
                          limb_states = {stable: NOT_EVALUATED, flex: NOT_EVALUATED}
topology hash failure     INVALID_EVENT_ALIGNED_AUDIT
real qualifying counts    SOURCE_EVENT_SUPPORT_INSUFFICIENT
real Part-A block         PART_A_CONTRADICTION
both limbs invariant      PRIMARY_G_DEGENERATE
                          [FOCAL_KEEP_SET_COMPONENTS_EXACTLY_INVARIANT]
```

Both frozen reason codes now reach an artifact from real data. Before D' they
existed **only in a stale `.pyc`** and appeared nowhere in `scripts/`.

`NOT_EVALUATED` — the fifth per-limb state outside the contract's frozen
four-state vocabulary — is observed on the real path, in the payload, on the one
branch that can carry it. It remains an implementation binding owed to Pro as
disclosure.

## What was steered, and what was not

Steered: the per-topology `U*` contributions, the Part-A `D_A` contrast, the
qualifying-episode counters, and the specific structure each precedence branch
reads. Untouched: the assembler, the bootstrap at its frozen iteration count, the
resolvers, and every unit's real component records, arm-distinctness pairs and
episode-world provenance.

**Two cases deliberately keep real values** so the gates are shown holding rather
than bypassed: `branch 2` leaves the real qualifying counts (one episode per limb
against a gate needing four across six topologies), and `branch 4` leaves the real
Part-A block.

## Two errors this cost, both in the exercise, neither in the instrument

**The limbs are mirrored and I used one `U*` map for both.** Stable `MATERIAL` is
`UCB95 < -5`; flex `MATERIAL` is `LCB95 > +5`. Every flex case came back
`AFFIRMATIVE_NONMATERIAL` regardless of what was requested — **the steering had no
effect and nothing said so**. The mirror is the science, not a convention:
material stable *persistence* means SET is worse than KEEP; material flex
*renewal* means SET is better. Same sign asymmetry recorded earlier this session,
in the opposite direction.

**`PART_A_CONTRADICTION` fires when the two arms are EQUIVALENT** — both
`LCB95(D_A + 5) > 0` and `LCB95(5 - D_A) > 0`. The name reads backwards until the
reason is visible: if the source were necessary, full sync should differ. The real
dev unit's `D_A ≈ 0.46` is inside the margin, so it contradicts legitimately and,
sitting above the combined result in the precedence, masked all nine.

Both were found by the exercise returning two distinct outcomes instead of
thirteen. Neither would have been visible from reading the code.

## Cost

Bootstrap at the frozen `BOOTSTRAP_ITERS` across sixteen assembled cases: about
forty minutes of CPU per run. `BOOTSTRAP_ITERS` was **not** reduced — with
identical replicated topologies the interval collapses to a point, so the
iteration count is numerically irrelevant here and lowering it would buy speed by
weakening the thing being exercised.

## Disposition

Step E closes. R4 closure steps A–E are complete. The formal R4 measurement
remains gated behind the separate conclusion-bearing compute authorization, and
`D7.3`/`D8` remain blocked pending a valid fresh-population R4 result.

## Verbatim output

Archived here rather than as a sibling .txt: the repository's bare-file ignore
rule excludes it, and `git add -f` is forbidden.

```text
case                                                    branch
----------------------------------------------------------------------------------------------
MATERIAL / MATERIAL                                     PERSISTENCE_NECESSARY_SOURCE  {'stable': 'MATERIAL', 'flex': 'MATERIAL'}
MATERIAL / AFFIRMATIVE_NONMATERIAL                      STABLE_PERSISTENCE_WITHOUT_MATERIAL_FLEX_RENEWAL  {'stable': 'MATERIAL', 'flex': 'AFFIRMATIVE_NONMATERIAL'}
MATERIAL / UNRESOLVED                                   MATERIAL_STABLE_PERSISTENCE_IDENTIFIED  {'stable': 'MATERIAL', 'flex': 'UNRESOLVED'}
AFFIRMATIVE_NONMATERIAL / MATERIAL                      FLEX_RENEWAL_WITHOUT_MATERIAL_STABLE_PERSISTENCE  {'stable': 'AFFIRMATIVE_NONMATERIAL', 'flex': 'MATERIAL'}
AFFIRMATIVE_NONMATERIAL / AFFIRMATIVE_NONMATERIAL       NO_MATERIAL_SOURCE_NECESSITY_IDENTIFIED  {'stable': 'AFFIRMATIVE_NONMATERIAL', 'flex': 'AFFIRMATIVE_NONMATERIAL'}
AFFIRMATIVE_NONMATERIAL / UNRESOLVED                    NO_MATERIAL_STABLE_PERSISTENCE_IDENTIFIED  {'stable': 'AFFIRMATIVE_NONMATERIAL', 'flex': 'UNRESOLVED'}
UNRESOLVED / MATERIAL                                   MATERIAL_FLEX_RENEWAL_IDENTIFIED  {'stable': 'UNRESOLVED', 'flex': 'MATERIAL'}
UNRESOLVED / AFFIRMATIVE_NONMATERIAL                    NO_MATERIAL_FLEX_RENEWAL_IDENTIFIED  {'stable': 'UNRESOLVED', 'flex': 'AFFIRMATIVE_NONMATERIAL'}
UNRESOLVED / UNRESOLVED                                 SOURCE_NECESSITY_UNRESOLVED  {'stable': 'UNRESOLVED', 'flex': 'UNRESOLVED'}
COMPONENT_INVARIANT / MATERIAL                          FLEX_RENEWAL_WITHOUT_MATERIAL_STABLE_PERSISTENCE  {'stable': 'COMPONENT_INVARIANT', 'flex': 'MATERIAL'}
MATERIAL / COMPONENT_INVARIANT                          STABLE_PERSISTENCE_WITHOUT_MATERIAL_FLEX_RENEWAL  {'stable': 'MATERIAL', 'flex': 'COMPONENT_INVARIANT'}
branch 1: component audit missing                       INVALID_EVENT_ALIGNED_AUDIT  [MANDATORY_PRIMARY_G_COMPONENT_AUDIT_MISSING]  {'stable': 'NOT_EVALUATED', 'flex': 'NOT_EVALUATED'}
branch 1: topology hash failure                         INVALID_EVENT_ALIGNED_AUDIT  {'stable': 'MATERIAL', 'flex': 'MATERIAL'}
branch 2: real qualifying counts, support insufficient  SOURCE_EVENT_SUPPORT_INSUFFICIENT
branch 4: real Part-A block, arms equivalent            PART_A_CONTRADICTION  {'stable': 'MATERIAL', 'flex': 'MATERIAL'}
branch 3: both limbs exactly invariant                  PRIMARY_G_DEGENERATE  [FOCAL_KEEP_SET_COMPONENTS_EXACTLY_INVARIANT]  {'stable': 'COMPONENT_INVARIANT', 'flex': 'COMPONENT_INVARIANT'}

distinct outcomes observed: 13
  FLEX_RENEWAL_WITHOUT_MATERIAL_STABLE_PERSISTENCE
  INVALID_EVENT_ALIGNED_AUDIT
  MATERIAL_FLEX_RENEWAL_IDENTIFIED
  MATERIAL_STABLE_PERSISTENCE_IDENTIFIED
  NO_MATERIAL_FLEX_RENEWAL_IDENTIFIED
  NO_MATERIAL_SOURCE_NECESSITY_IDENTIFIED
  NO_MATERIAL_STABLE_PERSISTENCE_IDENTIFIED
  PART_A_CONTRADICTION
  PERSISTENCE_NECESSARY_SOURCE
  PRIMARY_G_DEGENERATE
  SOURCE_EVENT_SUPPORT_INSUFFICIENT
  SOURCE_NECESSITY_UNRESOLVED
  STABLE_PERSISTENCE_WITHOUT_MATERIAL_FLEX_RENEWAL

STEP_E_ASSEMBLED_PATH_OK -- every registered outcome reached from the real dev-topology unit through the production reconstruction path.
```

## Forward pointer, added 2026-07-29

The `D_A ~ 0.46` recorded above as an obstacle to be steered around was **the
result arriving early**. The eight-topology formal population returned
`D_A = 0.484` and branched `PART_A_CONTRADICTION` for exactly the same reason.

The dev topology was not an outlier and this note held the signal without
recognising it. See
`20260729_D7_S_R4_THE_CONTROL_SAYS_THE_ARMS_ARE_EQUIVALENT.md`.
