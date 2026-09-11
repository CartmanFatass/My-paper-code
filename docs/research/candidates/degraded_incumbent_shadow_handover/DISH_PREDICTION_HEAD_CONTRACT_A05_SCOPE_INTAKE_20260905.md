# A05 pre-execution scope intake — 2026-09-05

**Object-tier technical decision:** keep the complete frozen A05 measurement and try
one simpler implementation layout, placing the probe directly in its object runner.
No scope waiver, new scientific quantity or execution is selected. The unaccepted
draft remains historical source; A04 and the existing family remain unchanged.

## What was checked

Read the original card `001e129b4`, CM scope return
`fb89b97214e8698ac911a61269c7a2f5b5940948` and all unaccepted Python source at
`9cd26782763b55c0d81ae4317fbfea7f83ff693e` on independent branch
`codex/impl-n3-dish-head-a05-20260905`. No model, compiler, test or result has run;
the accepted CM source branch contains the technical record, not this draft.

The first layout had 86/216 orchestration lines, 39.81%. After removing cache/hash
preparation and duplicate publication scaffolding, independent review reports
76/206 = 36.89%, still above the card's less-than-30% bound:

| Unaccepted file | Total non-test lines | Named orchestration ranges / count |
| --- | ---: | --- |
| direction/head_contract_a05.py | 154 | 1–15 and 49–59 / 26 |
| direction/head_contract_a05.cpp | 5 | 1–5 / 5 |
| scripts/run_dish_prediction_head_contract_a05.py | 47 | 1–12 and 15–47 / 45 |

The 58 test lines are excluded. All four protected 818b2566 production surfaces are
unchanged. CM/reviewer found no additional concrete semantic defect, but that cannot
make a scope breach accepted. No failure polarity or incomplete scientific attempt
is inferred, because no result-bearing invocation occurred.

The compiler cache would have removed the formal invocation's required compile after
the smoke populated it. The unaccepted draft already replaces that with a direct
one-shot compiler call into its own output and one load. That correction preserves
the existing card; it is not an accepted result or new experimental condition.

## Decisions this intake produces

Options: **(a), recommended**, consolidate the probe and CLI into one small object
runner, retaining the thin C++ measurement export and every frozen readout; (b) revise
the scientific card to drop a component; (c) return the unchanged unaccepted source
at a clean boundary. Select **(a)**. The current split pays for separate wrappers,
imports and handoff functions; consolidating them is a concrete implementation change
that can preserve all three scientific comparisons. Dropping an informative comparison
is premature while this simpler layout is untried.

Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**.
Reversible technical choice, **OWNER_DELEGATED**, owner flag `none`.

Only the card's owned-layout wording is clarified. The model/seed, inputs, real calls,
graph positive control, nine native calls, precision, outputs, branches, cost/cap,
source protection, admission and test profile remain unchanged. No new owner item is
created for this routine technical choice under the OWNER_DIRECT P2 cutoff; the genuine
existing new-card item is still 20260905-dish-018.

This is a bounded implementation attempt, not advance acceptance. CM must count the
actual final source and preserve readable code. Do not omit values or negative branches,
pad scientific lines, compress statements merely to manipulate a line count, move
machinery into another new file to conceal it, or reclassify the returned ranges without
a concrete reason. If this layout still exceeds the budget, return its named excess;
no violating verification or result is authorized. A genuine reduction of scientific
scope would be a separate prospective object-tier decision.

The existing one smoke/rule profile may adapt its import path to this layout; no
additional probe or repeated suite is introduced. There is still no accepted handle.
Root owns integration and the shared audit; original source and its budget history stay
recoverable on their pushed branches. Owner reviews CLI at this boundary returned `[]`.

## Append-ready audit for Root

Anchor `n3-prediction-head-contract-a05-scope`.

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T12:49:10Z | degraded_incumbent_shadow_handover (N3) | object | technical | a consolidated runner preserving all quantities; b reduced scientific card; c unchanged unaccepted boundary | a; no waiver or launch | yes | OWNER_DELEGATED, 2026-09-03 instruction | docs/research/candidates/degraded_incumbent_shadow_handover/DISH_PREDICTION_HEAD_CONTRACT_A05_SCOPE_INTAKE_20260905.md | none | |

## Final single-consolidation return — 2026-09-05

The one authorized layout attempt has ended. Final unaccepted source is
`ea05e9308e9e417d610e5cd41c66a4df91883c23`, on the same independent implementer branch
and worktree. CM's accepted branch contains only the additional technical record
`d24022f1c2e2d868ea714a0308ddb04760551fba`; the unaccepted code is not merged there.
Both worktrees are clean and pushed. No model, compiler, test or result has executed,
and no accepted process handle exists. There is no A05 scientific result.

DM read the complete final CM return, the named ranges in the consolidated source,
and its actual diff. The source has 185 runner lines and the unchanged 5-line thin
C++ translation unit: 190 non-test lines. Tests remain 58 lines, with only their
import adapted. Independent reviewer confirms **65/190 = 34.21%** orchestration:

| File | Named orchestration ranges | Count |
| --- | --- | ---: |
| scripts/run_dish_prediction_head_contract_a05.py | 1–14; 49–59; 114–122; 160–185 | 60 |
| direction/head_contract_a05.cpp | 1–5 | 5 |

Versus docs-bound draft `476194911`, the separate module loses 154 lines, the runner
adds 141/removes 3, and tests add 1/remove 1: aggregate +142/-158. The classifications
were retained. Savings came from imports and wrapper/handoff removal, with no scientific
padding or omitted quantities. All real calls, raw values, controls, branches, backward
passes, helper invocations and timing requirements remain. DM also compared the four
protected production paths against `818b2566`: no byte difference. Reviewer reports no
additional concrete semantic issue; runtime conformity remains untested.

### Decision this return produces — object / technical

Options: **(a), recommended**, retain the complete unexecuted card and exact draft,
stop local compression and return this recoverable boundary to Root; (b) replace the
scientific question with a reduced card solely to fit the current percentage. Select
**(a)**. The permitted simplification is complete, and the return contains no scientific
observation justifying removal of a comparison. No further reduction round, denominator
inflation, scope waiver or violating launch is selected.

Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**.
Reversible technical disposition, **OWNER_DELEGATED**, owner flag `none`.

At this boundary Root's current Portfolio explicitly records its reuse/deletion-ratio
proposal as pending, not an engineering-rule amendment. The immutable Pro packet predates
this final A05 draft. This intake supplies later technical evidence; it does not pretend
the packet included it, endorse a Portfolio decision or apply a proposed exception.
Current owner reviews CLI returns `[]`; no new P3/P4 inbox item is created.

The A05 question, A04 valid reconstruction and existing PRO_FINAL CONTINUE family remain
intact. This is an execution boundary, not a direction/family PARK, negative, RECAST,
priority or lifecycle decision. Root may drive other admitted work while addressing
the engineering conflict. Concrete updated authority or a separately justified object
decision can resume the same saved chain; merely awaiting an ACK is not a blocker.

### Append-ready final-return audit for Root

Anchor `n3-prediction-head-contract-a05-final-scope-return`. The minimum additional
integration is CM doc-only `d24022f1c` then this intake update; assembly merge `66a0b37d5`
is unnecessary once `fb89b9721` and DM `675cbe5ff` have been integrated. Do not integrate
the unaccepted code as accepted source.

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T12:54:46Z | degraded_incumbent_shadow_handover (N3) | object | technical | a retain full card and return exact unaccepted boundary; b reduce scientific question only for percentage | a; no further compression or execution | yes | OWNER_DELEGATED, 2026-09-03 instruction | docs/research/candidates/degraded_incumbent_shadow_handover/DISH_PREDICTION_HEAD_CONTRACT_A05_SCOPE_INTAKE_20260905.md | none | |
