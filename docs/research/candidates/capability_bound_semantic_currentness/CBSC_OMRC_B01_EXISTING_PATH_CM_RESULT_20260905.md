# CBSC B1 existing publisher cut: CM result

Date: 2026-09-05. Engineering only. **Source unaccepted; no runtime acceptance.**

The single concrete in-place candidate exceeds the frozen orchestration budget:
**64/94 = 68.09%**, using the independent reviewer's generous computation allowance.
The assignment's stop branch applies. This finding rejects these exact bytes, not every
possible existing-path repair, and supplies no scientific polarity or lifecycle decision.

## Contract and durable source

Controlling objective: `CBSC_OMRC_B01_EXISTING_PATH_SELECTION_INTAKE_20260905.md`
at DM commit `783bbeb3`. Runtime base:
`e4c0c93c76997cd8a74c1ff90d4e2cb2653c2fa6`.
`git diff e4c0c93c76997cd8a74c1ff90d4e2cb2653c2fa6 783bbeb3 -- experiments/candidates/capability_bound_semantic_currentness/omrc_b01 scripts/run_cbsc_omrc_b01_b1.py`
was silent: the intervening DM documentation did not change this runtime surface.

CM source commit: **`9350691811ec8ad87066b1422144c068fbfb8bd9`**,
branch/upstream `codex/cm-cbsc-gate-removal-20260905` /
`origin/codex/cm-cbsc-gate-removal-20260905`, tree
`C:/Projects/HMASD-worktrees/cm-cbsc-gate-removal-20260905`.

Implementer preservation commit: **`97d62f204f2ce001baf3210ea5228ded7e619685`**,
branch/upstream `impl-cbsc-gate-map-20260905` /
`origin/impl-cbsc-gate-map-20260905`, tree
`C:/Projects/HMASD-worktrees/impl-cbsc-gate-map-20260905`.
CM performed explicit-path commits and immediate pushes in both owned trees. Both pushes
succeeded; immediately before this report, both `git status --short` outputs were empty
and each HEAD equaled its upstream. Candidate working-file bytes matched between trees.

Only `experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_production.py`
changed in either source commit. Prior rejected candidates and original r01-r07 evidence
were untouched. Do not integrate either source commit. This report is a separate docs-only
commit for explicit report-only integration.

## Actual diff and independent review

Independent native reviewer:
`/root/dm_amx_cbsc_continue/cm_am_cbsc_direct_path/rev_ah_cbsc_direct_scope`
(`hmasd-reviewer`). Evidence locator: its 2026-09-05 final answer beginning
“Actual diff matches the coherent proposal; material scope finding remains”. This section
preserves that actual-diff review for recovery without live agent state. The review inspected
the finalized implementer working diff against the runtime base and contract above.

`git diff --numstat` observed **3 additions and 91 deletions**. `git diff --check`
was silent and exited zero. The code was not executed.

| Actual change | Baseline lines | Candidate location |
| --- | --- | --- |
| Delete first facts/descriptor/mechanical block | 1890–1913 | after 1889 |
| Delete duplicate reconstruction and local refusals | 1918–1974 | after 1893 |
| Use original training packet for final facts | 1988 | 1907 |
| Use original training packet for final descriptor | 1995 | 1914 |
| Use original training packet in final computation | 2005 | 1924 |
| Delete final local aggregate refusal | 2008–2014 | after 1926 |

The three replacements change only `recomputed_training` to `training_packet`.
Counting includes additions and deletions and excludes tests/docs. There are 88 outright
deleted lines and three replacements counted on both sides, hence 94 changed runtime lines.

Exact orchestration deletions are baseline **1890–1908 (19), 1918–1930 (13),
1949–1954 (6), 1960–1974 (15), 2008–2014 (7)**: 60 lines. Both sides of replacements
**1988→1907** and **1995→1914** contribute four more, yielding **64/94 = 68.09%**.

Generous scientific-call allowance: deleted **1909–1913 (5), 1931–1948 (18),
1955–1959 (5)**, plus both sides of **2005→1924 (2)**: 30 lines. These calls have mixed
responsibilities; crediting them in full favors the candidate. Treating the last parameter
replacement as orchestration instead yields **66/94 = 70.21%**. Either exceeds **<30%**.

There is no scientific-code copying or denominator padding. The new-source line budget passes
and the runner is unchanged. `scope: none` means no new section 4 machinery was added; it does
not mean section 5 budget conformance. No new wrapper, supervisor, registry, witness, retry,
resource service or schema layer was introduced.

CM accepts the review finding and stops here. The explicit closeout assignment does not require
finishing the other gates merely to make a scope-ineligible candidate appear ready.

## Structural observations and remaining dependencies

Initial complete table construction, materialized table reading, original summary generation
and one final mechanical computation remain structurally present. The candidate removes the
specified duplicate assembly/mechanical computation and local refusal blocks. This is static
data-flow inspection, not demonstrated preservation of all measurements or output equivalence.

The broader gate-removal objective is **not complete**:

- Unchanged `b1_metrics_artifact.py:1783–1803` still reconstructs and rejects mechanical
  disagreement on the downstream publication path.
- Upstream source/law/resource bindings remain, including production's original
  `_direct_invocation_groups` call at baseline 1766 and authority-witness entry at 2043–2073.
- `b1_metrics_training_assembly.py:343–348` and `449–456` require complete telemetry;
  `464–467` and `727–730` index measurements directly. Lines `2152–2167` and `851–858`
  couple work integrity to telemetry, so actual learner work must remain independently checked
  in any later repair.
- `b1_mechanical.py:640–646` rejects null measurements; `932–943` includes resource/digest
  predicates in completeness. Existing supervisor telemetry failure handling in `b1.py` still
  kills/refuses on initialization/poll failure and invokes strict final telemetry validation.

No claim is made that null resource handling, full fifteen-table publication, downstream
compatibility, or learner/scientific integrity has been verified. No scientific algorithms,
arm/seed selection, FP32/RNG/PPO/checkpoint source, quantity definition, or interpretation rule
was intentionally changed; correctness of the changed caller remains unexecuted and unaccepted.

## Protected source and zero-run facts

A local static byte comparison checked the 37 unchanged protected files: all pre-existing
`omrc_b01` files except the one owned modified module, plus the existing B1 runner. Git checkout
filters were applied to the baseline to account explicitly for Windows line endings:

```python
from pathlib import Path
import subprocess
base = 'e4c0c93c76997cd8a74c1ff90d4e2cb2653c2fa6'
prefix = 'experiments/candidates/capability_bound_semantic_currentness/omrc_b01'
changed = prefix + '/b1_metrics_production.py'
paths = subprocess.check_output([
    'git', 'ls-tree', '-r', '--name-only', base, '--', prefix,
    'scripts/run_cbsc_omrc_b01_b1.py'
], text=True).splitlines()
protected = [p for p in paths if p != changed]
mismatches = [p for p in protected if subprocess.check_output([
    'git', 'cat-file', '--filters', base + ':' + p
]) != Path(p).read_bytes()]
print(len(protected), mismatches)
```

Observed: **37 files, zero mismatches**, exit zero. CM inspected the entire actual modified
module diff and confirmed it contained only the specified deletion/replacement cut. This is a
source-surface comparison, not a commit-identity guard or runtime proof.

**Zero** smoke, focused suite, r05 offline publication, new resource receipt, remote profile,
learner invocation, r08, or experiment handle was created. No tracker handoff was needed.
No resource performance was measured, and no runtime failure was classified. The prior
243.55-second focused/offline allowance remains unspent by this slice. Historical cost projections
are not measurements of the changed route. All commands were bounded local editing, static
inspection, Git preservation and report production; no owned operation remains live at closeout.

Next step: DM records this exact bounded scope blocker and returns the slot to Root scheduling.
There is no accepted launch SHA and no inference that every alternative implementation is impossible.
