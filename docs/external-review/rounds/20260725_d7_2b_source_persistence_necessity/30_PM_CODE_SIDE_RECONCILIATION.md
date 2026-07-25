# PM reconciliation — D7.2B source persistence necessity

```text
ruling=21_PRO_OPEN_RAW.md   stage_commit c4c14175184f7fc31d7f15fae4e9d6e97e078bd2
verdict=ACCEPT the retirement, with the correction broadened in three ways
disputed=nothing
```

Pro accepted the retirement scope exactly as proposed and then widened it. The
widening is the valuable part, so it is recorded first.

## 1. What Pro corrected in my framing

**`U_opp` was misnamed, and I had been treating it as a source property.** Its
maximization runs under the frozen learned joint policy, so it is *best focal SET
under policy continuation*, not an oracle property of the source. Renaming is not
cosmetic — the whole D7.2B failure is that I had no source-level quantity, so
nothing in the estimand set could have detected the degeneracy before spending a
run.

A third estimand is required, with the other agents and later decisions
**reoptimized or supplied by a constructive oracle in both terms**:

```text
U*_{i,src}(h;H) = max_{z != z_i, joint continuation} E[G_H | SET_i(z)]
                - max_{joint continuation}          E[G_H | KEEP_i]

persistence-essential history requires
    U*_stable,src / B_H <= -0.10        and        U*_flex,src / B_H >= +0.10
```

On the retired toy `U*_stable,src = 0` exactly, because persistence and full-sync
swapping both attain the ceiling. **That single number is what a source gate would
have caught for free**, before any training.

Three layers now, and the result shows why each is needed: source-level necessity
`U*_src`; policy-conditional focal effect `U_pi` and `U_max_pi`; natural behaviour
(hazard and realized individual lifetime).

**My class constraint in Q3 was too broad and is replaced.** Permutation-invariant
reward alone does *not* imply role exchange substitutes for persistence — position,
energy, queue state, internal memory, transition latency or non-transferable
service state can all make persistence necessary under an anonymous reward. The
valid statement requires the *full future state over `H`* to survive the exchange,
not just immediate reward. A globally anonymous source stays usable when assignment
history is non-transferable.

**The optimum-selection reading is legitimate but parked**, not a carrier result.
Registered as `R30_ALL_SET_BASIN_INDUCTIVE_BIAS — retained hypothesis, parked`.
Establishing it needs multi-seed pre-registration with basin classification fixed
before training, and Pro is explicit that no runs should be spent on the
equal-optimum source to chase it.

## 2. Where Pro declined to rule, and it was right to

I asked in Q4 whether the main scenario shares the degeneracy, and flagged it as
the question I was least able to answer. Pro's answer: **the main-scenario
environment and its transition/reward contract were not in my evidence allow-list**,
so my "largely indifferent to which member serves demand" was an inference in the
question rather than a repository fact, and ruling on it would exceed the listed
evidence.

That is an authoring defect on my side, not a limitation of the reviewer. The
allow-list was built around the toy and the carrier; the question then asked about
a source that was not in it.

## 3. The successor changes — it is not a replacement toy

The immediate successor is **not** Q2's replacement control. It is:

```text
D7.S -- zero-compute main-scenario persistence-necessity audit
```

with three branches: main scenario passes → straight to D7.3 and **Q2 becomes
unnecessary**; fails → build the tenure control *and* redesign the main source;
unresolved → the tenure control advances carrier capacity only. **D8 stays blocked
in every branch** until the paper-level source is qualified. A positive toy cannot
rescue a main benchmark that does not require individual persistence.

Freeze before D7.S: the mixed-urgency history class, the external-return horizon,
the legal joint continuation, the source-level oracle or constructive controls, the
normalized persistence margin, and the three branch meanings
`PERSISTENCE_NECESSARY_SOURCE`, `ZERO_COST_ROLE_EXCHANGE_SOURCE`,
`SOURCE_NECESSITY_UNRESOLVED`.

## 4. If a replacement source is built — mechanism (a), modified

Tenure-dependent effectiveness as **non-transferable agent–duty state in the
dynamics**: the stable duty's effectiveness depends on continuous tenure of the
current agent–duty pairing, and transferring it resets or degrades the accumulated
state. This preserves permutation equivariance — permuting agents *and* their local
state leaves the source unchanged — while breaking zero-cost assignment exchange.
Anonymity is kept; only the free swap dies.

The consequence must enter external return through service or dynamics, **never** a
`-beta * SET` term. Pro rejected the direct switch cost as primary on exactly the
ground I flagged: it manufactures the measured effect inside the reward, and `U`
would then contain the penalty introduced to make `U` separate. It also rejected
asymmetric action support as tautological.

**Tenure may enter the controller state** as generic decision-time information —
commitment age, realized effectiveness/setup state, incumbent skill, task context.
A hidden tenure variable would make a negative ambiguous between temporal-control
failure and missing information. Still forbidden: `stable_role`, `relay`,
`service`, the future target change, or any KEEP/SET recommendation. Ground-truth
labels stay evaluator-only.

Ten conditions must hold and are to be **solved analytically or by constructive
controls before training**; a source failing the gate never consumes a carrier run.

## 5. On the competence budget — accepted, but not as a precedent

Pro accepted the budget escalation for this narrow result, on the grounds I
argued: A is a prerequisite, thresholds were untouched, the routing rule predated
the flat result, the checkpoint rule predated the audit — and, decisively, the
retirement follows by derivation and is independent of optimizer settings.

It does not generalize. The replacement needs a **pre-registered finite competence
ladder**: fixed initial exposure, predetermined escalation stages, a fixed maximum,
escalation only when the gate fails *and* liveness diagnostics show the policy has
not moved, no threshold/source/optimizer/checkpoint changes between stages, and
separate competence-development and audit episodes. If the maximum stage fails,
report no-access rather than continuing to raise budget until A passes.

This run also cannot support a search-efficiency comparison or a claim that the
default R30 budget is adequate.

## 6. Two documentation defects Pro caught, both fixed

Neither changes the ruling; leaving them would have let the small-sample artifact
survive as the active summary.

- `EXPLORATION_LEDGER.md` still carried the two-episode machinery values
  `0.214 / 0.232` where the registered result is `0.430 / 0.252`. Fixed.
- The evidence note's header said the final audit was pending while the final
  result appeared later in the same file. Fixed.

## 7. Code-side consequences

Nothing to implement yet — the ruling authorizes neither implementation nor
compute. What it changes in the repository:

| Item | Action |
|---|---|
| `U_opp` naming | Relabel to focal-best SET under policy continuation, in D0 and in the audit script's docstrings and result keys |
| `U*_src` | New source-level estimand; add to D0 with the `±0.10` margins |
| Source gate | New pre-freeze check: does an optimal all-SET continuation exist, does exchange preserve full future state over `H`, is any agent-local state lost, is best full-sync SET materially below optimal mixed |
| Class constraint | Replace my broad Q3 statement with Pro's narrow one wherever it was recorded |
| Ledger | D7.2B′ is not next; D7.S is. D8 blocked in all branches |
| Parked | `R30_ALL_SET_BASIN_INDUCTIVE_BIAS` as a retained hypothesis |

The audit script, forcing hook, CRN replay, event ledger and `B_H` all survive
unchanged and transfer to whatever source comes next.
