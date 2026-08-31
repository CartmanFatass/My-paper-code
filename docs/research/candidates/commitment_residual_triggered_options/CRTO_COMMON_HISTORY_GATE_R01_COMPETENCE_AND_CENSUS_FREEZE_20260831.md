# CRTO common-history gate R01 competence and census freeze

Date: `2026-08-31`

Object: `CRTO-COMMON-HISTORY-GATE-20260830-01`

Freeze status: `FINAL_FOR_CM`

## Conclusion

The two missing scientific objects are now prospectively defined without a seed-superpopulation
assumption.

`RAW-LONG` competence is a material-decision-balanced native-regret gate on the untouched fixed-K8
panel. It requires every one of the eight registered RAW checkpoints to be close to the exact G16
oracle separately when KEEP is materially preferable and when replanning is materially preferable.
An unstratified mean is invalid for this purpose: a policy that always keeps can have mean regret
only `0.2 * 0.02 = 0.004` when all material error is confined to the 20% replan-headroom rows.

The six representation-by-budget decisions use an exact fixed-eight-address census envelope. The
registered counter addresses are reproducible and isolated, but are not treated as an iid Normal,
exchangeable, or randomly sampled seed population. Student-t intervals have no decision authority.
This repair obtains a valid deterministic decision only by narrowing the estimand and claim to all
eight registered addresses and their exact panels.

## Question and non-goals

The smallest decision-relevant question is whether the aligned calibrated residual changes
finite-budget native action regret relative to a competent same-history RAW gate on the frozen
script-reachable common-history surface.

This freeze does not test information gain, hypothesis-class superiority, learned-policy return,
natural-policy occupancy, general seed robustness, variable-team MARL, warehouse or UAV value,
safety, or deployment. It does not rehabilitate B1 or the lost update-1,000 continuation.

The treatment is `TRUE_RESIDUAL`; the principal competent same-information null is `RAW`; intact
`CALIBRATED_DERANGEMENT` separates alignment from generic residual preprocessing; SHORT versus LONG
separates finite optimizer exposure. The logged deterministic script and the zero-regret row oracle
are reference policies, not additional learned arms.

The mechanism path is: an exogenous demand/sensor/K event changes deployable telemetry; one fixed
environment slot owns the active option and its continuous history; the frozen script creates the
occupancy history; the gate sees that 42-vector history plus exactly one RAW, aligned-residual, or
deranged packet; it selects KEEP or one legal replacement; the target pays the real action charge
once; and the frozen partner/target script then produces the common 16-step reward-and-potential
consequence. The gate never creates the history distribution on which it is audited.

This host has four persistent agents and no join, leave, rejoin, or entity replacement. Environment
slot identifies state ownership and canonical scanning only and is not an actor identity feature.
Accordingly, the result says nothing about variable membership, survivor state, censoring by agent
replacement, partner co-adaptation, or natural-policy occupancy.

## Inputs and direct observation

The accepted inputs are:

- `DIRECTION.md` and `IMPLEMENTATION_THRESHOLD.md`;
- `CRTO_B1_SCIENCE_CARD.md` and the exact-v4 preactivity intake;
- the probe-cut scope, synthesis, and review notes;
- the isolated common-history package and its current tests; and
- `docs/project/ALGORITHM_PRINCIPLES.md`.

Direct inspection establishes that the isolated evaluator already computes legal-action G16
regret, fixed-K8 regret, logged-script regret, per-regime target regret, and all six paired
representation-by-budget effects. Its current `bonferroni_t` route assumes the very seed-sampling
law that is absent. Fixed counter addresses establish deterministic separation of streams, not a
probability law for a seed superpopulation.

No untouched R01 confirmation result was observed while defining this freeze. Historical B1
decoder values govern a different endpoint and supply no numerical competence threshold here.

### Literature boundary

A read-only `2026-08-31` inventory of `C:/Projects/Inst-sci/papers/MyLib` found `190` PDFs and
`190` structured JSON records. Exact quick-index searches found no occurrence of `fixed seed`,
`counter-address`, `counter address`, or `seed superpopulation`, and no dedicated source that turns
fixed counter addresses into iid-Normal or exchangeable sampling units. The library's MARL material
contains many ordinary random-seed and confidence-interval usages, but none supplies the missing
target-population law for this object. This was a scoped local-index check, not an exhaustive
systematic review.

Two external primary references reinforce the need to state the statistical target and uncertainty
assumptions: Agarwal et al., *Deep Reinforcement Learning at the Edge of the Statistical Precipice*,
NeurIPS 2021 ([official paper](https://papers.nips.cc/paper/2021/file/f514cec81cb148559cf475e7426eed5e-Paper.pdf)),
and Patterson et al., *Empirical Design in Reinforcement Learning*, JMLR 25(318), 2024
([official article](https://www.jmlr.org/papers/v25/23-0183.html)). They motivate few-run caution and
assumption-explicit reporting. Neither paper authorizes an iid-Normal law for CRTO's fixed
counter-addressed slots, so neither is used as a sampling premise or numerical-threshold source.

## Frozen finite population, unit, and clocks

The finite target is exactly replicate addresses `0..7` under RNG namespace `2026083001`, their
preassigned predictor, calibration, training, and evaluation tapes, their addressed initializers
and orders, and the retained rows produced by the frozen boundary law. These eight slots are all
members of the target, not a sample from a larger population.

Within a slot, episodes and retained rows are nested measurements. The slot is the top-level unit.
For the six target effects, rows are averaged within fixed K16, `4->16`, and `16->4`; those three
regime means are equally weighted within the slot. Primitive time, review opportunity, commitment
age, predictor horizon, 16-step credit, optimizer update, and processed-row exposure retain their
existing distinct clocks.

No slot, episode, row, checkpoint, or address may be retried, replaced, selected, or dropped after
observation. Missing members invalidate the census rather than defining a smaller population.

## RAW-LONG competence

For every retained fixed-K8 row `i`, define

```text
A_i = max_{legal replacement a} G16(a;i) - G16(KEEP;i).
```

The competence strata are fixed before looking at gate actions:

```text
KEEP_MATERIAL   = {i : A_i <= -0.02}
REPLAN_MATERIAL = {i : A_i >= +0.02}.
```

Rows with `-0.02 < A_i < 0.02` remain in the formal representation contrasts but do not qualify
RAW competence. Endpoints belong to the displayed material strata.

Before competence is calculated, every slot must have all 64 preassigned unreplaced K8 episodes,
at least 48 retained boundaries, common row keys for all representations, finite legal G16 labels,
charge-once and 16-step common-future validity, and at least eight retained rows in each material
stratum. Any failure is `NONIDENTIFYING_K8_COMPETENCE_SUPPORT`.

Let the RAW-LONG selected action on row `i` be `a_RAW(i)` and define, for slot `s` and stratum `z`,

```text
R_RAW(s,z) = mean_i[max_legal_a G16(a;i) - G16(a_RAW(i);i)],  i in (s,z).
C_RAW      = max over s in 0..7 and z in {KEEP_MATERIAL,REPLAN_MATERIAL} R_RAW(s,z).
```

`RAW-LONG` is competent if and only if

```text
C_RAW <= 0.010000000000.
```

The scientific reference is exact oracle regret zero. The `0.01` ceiling is a new prospective G16
regret convention: on both sides of a registered material decision, the mean selected action must
remain within one half of the existing `0.02` material KEEP-versus-replan gap. It is not B1's
decoder-NMSE threshold and it is not inferred from development results. A comparison tolerance of
at most `1e-12` may absorb floating arithmetic; that tolerance is not a scientific margin.

The logged-script regret is computed and reported for the same sixteen slot-by-stratum cells,
together with signed `R_RAW-R_SCRIPT`, maxima, and row counts. It is the strongest simple
same-information behavioral diagnostic, but is not a competence gate. Making script superiority a
gate would conflate oracle-proximal comparator competence with a separate package-value question;
for example, an oracle script need not disqualify a RAW cell with regret `0.009`.
The script's `0.01*agent` score term is common to all candidate options for that agent and therefore
cancels from its action choice; it does not grant the script an action-selecting identity advantage.

All sixteen cells must pass. Seven-of-eight, a grand mean, a median, or compensation between KEEP
and REPLAN is forbidden. Failure after valid support is `STOP_RAW_LONG_INCOMPETENT`; TRUE and
DERANGED outcomes then have no residual polarity and must not be inspected or routed.

## Exact simultaneous census decision

For slot `s`, budget `b` in `{SHORT,LONG}`, and target-regime-equal regret `R`, define

```text
x_RT(b,s) = R_RAW(b,s)       - R_TRUE(b,s)
x_DT(b,s) = R_DERANGED(b,s) - R_TRUE(b,s)
x_RD(b,s) = R_RAW(b,s)       - R_DERANGED(b,s).
```

For each of these six contrast-by-budget coordinates, define the exact registered-address hull

```text
L_jb = min_s x_j(b,s)
U_jb = max_s x_j(b,s),       s = 0..7.
```

`[L_jb,U_jb]` contains the complete finite target vector by construction. It is an effect envelope,
not a confidence interval. The six hulls are observed simultaneously, so probability coverage,
family alpha, multiplicity correction, standard error, power, and iid assumptions do not apply.
Width measures registered-slot heterogeneity rather than sampling uncertainty. Report every slot,
the hull, and the equal-slot mean; the mean is descriptive and never routes a branch.

Before forming a contrast, every row-level native regret and every derived `R` value must be finite
and nonnegative. The three contrasts are derived from the same six base regret values rather than
accepted as independent inputs; in particular `x_RT=x_RD+x_DT` must hold by construction. Exactly
eight slots and every preceding structural/admission gate are part of `VALID`. A failed validity
predicate is `NONIDENTIFYING`, outside the branch table.

Set `delta=0.005` and define

```text
SUP(j,b) = (L_jb > delta)
EQ(j,b)  = (L_jb >= -delta and U_jb <= delta)
NO_TRUE_BENEFIT(b) = (U_RTb <= delta).
```

Equality at `delta` is not superiority; the endpoints `-delta` and `delta` are inside equivalence.
After all competence, calibration, structural, support, work, and resource gates pass, route the
first matching branch in exactly this order:

```text
PERSISTENT_ALIGNED_BIAS =
    SUP(RT,SHORT) and SUP(RT,LONG)
    and SUP(DT,SHORT) and SUP(DT,LONG)

GENERIC_PREPROCESSING =
    SUP(RT,SHORT) and SUP(RT,LONG)
    and SUP(RD,SHORT) and SUP(RD,LONG)
    and EQ(DT,SHORT) and EQ(DT,LONG)

OPTIMIZATION_EXPOSURE_ONLY =
    SUP(RT,SHORT) and SUP(DT,SHORT)
    and EQ(RT,LONG) and EQ(DT,LONG) and EQ(RD,LONG)
    and RAW_GAIN and TRUE_NO_MATERIAL_DEGRADE

CLOSE_TESTED_MECHANISM =
    NO_TRUE_BENEFIT(SHORT) and NO_TRUE_BENEFIT(LONG)

otherwise UNRESOLVED.
```

The two budget-trajectory predicates in that table are

```text
RAW_GAIN =
    min_s [R_RAW(SHORT,s) - R_RAW(LONG,s)] > delta

TRUE_NO_MATERIAL_DEGRADE =
    max_s [R_TRUE(LONG,s) - R_TRUE(SHORT,s)] <= delta.
```

These branches are mutually exclusive. The SHORT `SUP(DT,SHORT)` clause makes the optimization
branch aligned-specific rather than derangement-insensitive preprocessing. Requiring all three
LONG pairs to be equivalent prevents persistent alignment use from being mislabeled as
optimization-only. `RAW_GAIN` and `TRUE_NO_MATERIAL_DEGRADE` exclude another exact counterexample:
the RAW-TRUE gap can close solely because TRUE worsens while RAW remains unchanged. Without both
absolute-trajectory predicates, a budget-dependent contrast is `UNRESOLVED`, not RAW catch-up.

`CLOSE_TESTED_MECHANISM` follows the three positive explanations. Its `U_RT<=delta` law deliberately
includes material RAW superiority: it closes a material TRUE-over-RAW benefit, but does not claim
equivalence. If `U_RT < -delta`, the result must explicitly say that RAW is materially better on all
registered slots rather than describe the methods as equal.

Within a valid CLOSE result, label each budget separately as

```text
RAW_SUPERIOR             if U_RTb < -delta
PRACTICAL_EQUIVALENCE    if EQ(RT,b)
MIXED_OR_SMALL_TRUE_EFFECT otherwise.
```

These are descriptions inside CLOSE, not additional result opportunities. A combined equality
statement requires `EQ(RT,SHORT) && EQ(RT,LONG)`.

Any missing/nonfinite slot or incomplete six-coordinate family is `NONIDENTIFYING`; it cannot be
repaired with a t interval, bootstrap, sign flip, replacement address, or available-slot subset.
The existing Student-t calculation may be retained only as a clearly model-conditional descriptive
sensitivity analysis. It has no result-branch authority.

## Why Student-t is not repaired by Bonferroni

Bonferroni controls a family only when each marginal interval has its stated coverage. Without a
sampling law, that premise is absent. For a concrete counterexample, let an independently sampled
effect be zero with probability `0.9` and `0.1` with probability `0.1`. Eight observations are all
zero with probability `0.9^8 = 0.43046721`; the wave-2 zero-standard-deviation convention returns
the point interval `[0,0]`, which misses the population mean `0.01`. Multiplicity correction cannot
repair the invalid marginal model.

If a future object requires probabilistic generalization, it must prospectively sample roots from
an explicit target law. Even then, eight observations support only weak distribution-free objects.
For example, `[min,max]` covers a population median with marginal miss probability `2/2^8=1/128`;
six Bonferroni-unioned median intervals have family miss probability at most `6/128=0.046875`, but
they provide no finite-sample mean inference or narrow equivalence. That is a new population object,
not an alternate analysis of these fixed addresses.

## Development pilot

A smallest useful B-level feasibility pilot is permitted after CM implements the frozen calculation.
Its prospective registration is fixed as follows and is not caller-selectable:

```text
object_id = CRTO-COMMON-HISTORY-RAW-PILOT-20260831-01
rng_namespace = 2026083191
slots = (0,1)
claim_ceiling = TWO_SLOT_RAW_LONG_DEVELOPMENT_FEASIBILITY_ONLY
```

The pilot namespace is disjoint from confirmation namespace `2026083001`; a repository-wide
source search before registration found no prior use of either the pilot object ID or namespace.
The CLI may accept output and receipt paths only. It may not accept or override the object ID,
namespace, slots, checkpoint, threshold, row law, or population counts.

The registered pilot uses:

- the same predictor law, RAW gate, 2,048-update LONG checkpoint, and 64 fixed-K8 development tapes;
- the identical KEEP/REPLAN material strata, support counts, and `0.01` oracle-regret ceiling;
- no TRUE or DERANGED training or evaluation; and
- a fresh 4 GiB admission before any pilot RNG address or tape is constructed, followed by the
  result-blind structural scan, then a second fresh 4 GiB admission and same-envelope `assess-run`
  immediately before any Torch-dependent component, model, optimizer, scientific root, or result.

Every slot must retain all 64 preassigned fixed-K8 episodes, at least 48 audit rows, at least eight
rows in each material stratum, and finite charge-once G16 labels. The pilot is `PILOT_FEASIBLE`
only if all four slot-by-stratum RAW-LONG mean regrets are at most `0.01`. A support failure is
`NONIDENTIFYING_PILOT_K8_SUPPORT`; a complete supported failure is
`PILOT_RAW_LONG_INCOMPETENT`. There is no averaging or compensation across slots or strata.

The pilot can reveal missing two-sided support, gross RAW learnability failure, runtime, or an
implementation defect before paying for all six confirmation cells. It cannot inspect the final
eight addresses, choose or alter `0.02`, `0.01`, `0.005`, 2,048 updates, checkpoint, row law, or
address, and cannot substitute for confirmation. A pass establishes feasibility only. A valid fail
updates that development architecture-budget object, not the untouched fixed-eight confirmation;
any scientific repair requires a new prospectively named object and fresh confirmation addresses.

The durable pilot receipt must state the exact object ID, namespace, slots, `RAW`-only arm set,
LONG-only decision checkpoint, support counts, four competence cells, both memory admissions, the
post-scan `assess-run`, work facts, outcome, and the literal claim ceiling above. It must also state
that confirmation namespace
`2026083001` was not instantiated and that no TRUE/DERANGED model, checkpoint, evaluation, effect
hull, or representation polarity was produced. `PILOT_FEASIBLE` supports only executable
two-slot RAW-LONG feasibility. Neither pass nor fail estimates confirmation success probability,
generalizes to another address, or supplies information, residual, optimization, policy-return,
MARL, promotion, or closure evidence. An incomplete implementation is quarantined and consumes
neither this pilot object nor the confirmation object under the repository-wide incomplete-attempt
rule.

## Judgment impact and claim ceiling

The two former scientific blockers are resolved prospectively. This does not make the current code
or resource ledger conformant and does not itself create a result. CM must implement the material
strata, all-slot gate, exact hulls, branch truth table, complete ledger, runtime counters, and
resource checks before any final run.

The maximum result claim is uniform only over the eight registered addresses, their frozen
script-reachable retained rows, the three equally weighted target regimes, the fixed supervised
budgets, and 16-step G16 action regret. It says nothing probabilistic about another seed, address,
tape, optimizer draw, policy occupancy, or environment.
