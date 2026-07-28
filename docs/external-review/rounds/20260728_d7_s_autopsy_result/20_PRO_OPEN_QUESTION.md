# D7.S normalizer autopsy — the result, and one decision the instrument is blocked on

The autopsy you converged has run. It is artifact-only; no environment compute
was used. This is the result submission.

**One thing is genuinely blocked and needs your decision to unblock**: the
instrument can no longer emit any non-degenerate branch, because the aggregation
rule from per-continuation sequence equality to a per-limb
`components_separate` does not exist and is not mine to invent. §4.

## Frozen inputs — not review surface

- The disposition `PRIMARY_G_DEGENERATE`, the retired smallest unit, and your
  prohibition list. Not reopened.
- The six modifications, all implemented. The recorded R3 artifact is
  byte-unchanged.
- The autopsy's numbers are offered as claims to falsify against the artifact,
  not as premises. Discarding this question's framing is a legitimate answer.

## 1. The sentinel passed, so the rest is readable

All six fail-closed conditions held, including **exact reproduction of the six
registered R3 bounds**. Your Modification 2 turned my one-off manual 1e-12 check
into a precondition the analysis cannot start without; it now gates every
statistic below.

Confidence: I verified the bound reproduction independently before the script
existed, and the script reproduces it through the same `compute_t_m_bootstrap`
the run used rather than a second implementation.

## 2. Section A — standalone distributions

| artifact-derived | point | 5th pct | 95th pct | min | max | +/−/0 |
|---|---|---|---|---|---|---|
| `B_stable` | +0.180139 | −0.077367 | +0.416071 | −0.495793 | +0.534832 | 5/1/2 |
| `B_flex` | +4.288854 | −8.648833 | +14.102587 | −17.147505 | +19.027850 | 6/2/0 |
| `U*_stable` | +1.254074 | −2.203652 | +7.186347 | −5.205364 | +14.042137 | 4/4/0 |
| `U*_flex` | −4.122402 | −13.827640 | +3.371472 | −30.069646 | +7.395372 | 3/5/0 |

The 5th percentiles of the two `B_m` intervals are exactly the recorded one-sided
LCBs, which confirms the two-sided presentation is the same distribution rather
than a re-derivation.

## 3. The evidence matrix — N5 is raised

| Explanation | Verdict |
|---|---|
| N1 signed-normalizer failure | compatible (moderate tier) |
| N2 opposite source direction | not resolved |
| N3 component cancellation | `UNDISCRIMINATED_FROM_STORED_ARTIFACT` |
| N4 topology heterogeneity | material (`max R_topology = 0.1221`) |
| **N5 comparator-scale mismatch** | **raised** |
| Selection instability | moderate (39% / 37% of events below 0.60) |

**N5 is raised on an essentially absent association.** Per-topology paired
`(B_m, U*_m)`: stable `pearson +0.038`, `rank −0.180`; flex `pearson +0.022`,
`rank −0.333`.

**Project Manager inference, marked as such:** this reads as stronger than "the
normalizer is weak." Across topologies `B_m` carries close to no information
about `U*_m`, and what little rank association exists points the wrong way. If
that holds, the denominator was arguably never the right denominator — a design
fault rather than a power fault, consistent with §9 having independently
forbidden expansion. **That is my reading of your N5, not a result**, and the
eight-topology sample makes any association estimate unstable, exactly as you
warned when you said no association test should be a sharp acceptance gate.

N4 is material but not dominant, and per Modification 5 establishes no regime.
N3 carries your required sentence verbatim and is not scored false or lowered.

## 4. The blocker — the instrument now refuses every non-degenerate branch

Implementing your COMPONENT_INVARIANCE tri-state had a consequence I want in
front of you rather than discovered later.

`decide_branch` now takes `component_invariance_evaluated` with **no default**,
and `assemble_audit_result` defaults it **False** — the fail-closed direction, so
that forgetting it can only make the instrument stricter. The arriving
implementation had defaulted it `True`, which is fail-open and structurally the
same defect as the hardcoded `False` this repair removed; I rejected that and
watched the corrected guard go red before accepting it.

The consequence is exactly what you specified — *"later branches cannot fire on a
future run whose mandatory component audit is missing"* — so **no run can now
resolve to branches 4–10.** Component persistence and per-paired-continuation
exact sequence equality are implemented and computed before serialization. What
is missing is the step from those per-continuation booleans to a single per-limb
`stable_components_separate` / `flex_components_separate`.

That aggregation rule is a threshold that decides which branch fires, so I did
not invent it. Candidates, offered without preference:

- **all-invariant** — a limb is *not* separate only if every paired continuation
  was exactly equal;
- **any-separate** — a limb is separate if any paired continuation differed;
- **a fraction** — separate if more than some proportion differed, which needs a
  number you would have to set.

Until this is decided the instrument is fail-closed and cannot produce an
affirmative result. That is a safe state, not a broken one, but it is a stop.

## 5. Context you should have: the evidence this rests on

The back-half mutation sweep is unchanged since your last ruling and its scope
still applies. Every number above is conditional on the R3 execution path being
correct, and the suite would not have detected several ways it could be wrong —
including a halved `g_total`. The autopsy cannot repair that, because the
component series that would allow independent reconstruction were never
persisted. It inherits the conditional scope you named.

## What is asked

**Q1 — the smallest unit.** What does this autopsy retire or support, at the
smallest unit it actually settles? Does N5 raised move the portfolio, or is an
eight-topology association too unstable to move anything?

**Q2 — the next action.** Freeze an R4 measurement with a treatment-independent
positive scale, or retire S7-S3 as the carrier of this proposition? If R4, does
N5 raised constrain what the replacement scale may be — specifically, must it be
matched to the focal one-Δ intervention rather than to a global-rotation
contrast?

**Q3 — the blocked aggregation rule.** Which rule maps per-continuation exact
sequence equality to a per-limb `components_separate`? A rule, or an explicit
instruction that the instrument should stay fail-closed until R4 is frozen.

**Q4 — selection instability.** With 39% / 37% of events below a 0.60 leading
candidate frequency, is the `2/2` floor itself implicated in the breadth of the
`U*` intervals, or does that stay a qualifier?

## Required response sections

```text
1. SMALLEST_UNIT       what the autopsy retires or supports
2. NEXT_ACTION         R4 scale or carrier retirement, and what it would decide
3. AGGREGATION_RULE    the components_separate rule, or stay fail-closed
4. SELECTION_FLOOR     whether 2/2 is implicated
5. CHALLENGES          which claims above you checked and found wrong
```

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260727_d7_s_normalizer_autopsy_plan/21_PRO_OPEN_RAW.md`
- `logs/d7s_autopsy_1/d7s_normalizer_autopsy.json`
- `logs/d7s_autopsy_1/d7s_normalizer_autopsy.md`
- `scripts/d7s_normalizer_autopsy.py`
- `scripts/audit_d7_s_event_aligned.py`
- `docs/research/cdc/EVIDENCE_NOTES/20260728_D7_S_THE_NORMALIZER_IS_UNRELATED_TO_THE_EFFECT.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md`
