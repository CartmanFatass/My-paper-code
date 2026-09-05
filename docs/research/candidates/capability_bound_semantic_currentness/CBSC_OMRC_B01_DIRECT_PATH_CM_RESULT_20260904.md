# CBSC B1 direct path: CM scope-blocker return

Date: 2026-09-04. Evidence role: engineering only; no scientific result.

The concrete candidate is **unaccepted and incomplete**. Its independently counted
orchestration share exceeds the frozen below-30% limit. This rejects these source bytes;
it does not prove every possible direct implementation infeasible. No runtime acceptance,
scientific preservation certification, or authorization to launch B1/r08 follows.

## Assignment and preserved candidate

The controlling assignment is
`CBSC_OMRC_B01_DIRECT_PATH_SELECTION_INTAKE_20260904.md`, bound at
`1cbad766a973641e3cac2747129621331750b840`. It requests learner/helper reuse, complete
fifteen-table publication with the original null interpretation boundary, and a real-count
offline r05 profile, with a stop branch for a concrete scope breach.

Rejected candidate SHA: `908729835c762bc1d75120168fa65bd13875b6a2`.
Branch and upstream: `codex/cm-cbsc-direct-20260904` and
`origin/codex/cm-cbsc-direct-20260904`.
CM worktree: `C:/Projects/HMASD-worktrees/cm-cbsc-direct-20260904`.
The candidate commit was pushed successfully. Before this report was written,
`git status --short` and `git diff HEAD --stat` were empty, and `git rev-parse HEAD`
and `git rev-parse '@{upstream}'` both returned the candidate SHA.

The candidate changes only:

- `experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_direct.py`
- `scripts/run_cbsc_omrc_b01_b1_direct.py`

Both explicitly carry `INCOMPLETE_NOT_RUN`. Preserve the candidate branch for inspection;
do not cherry-pick its source commit into the production target. This report is delivered
in a separate docs-only commit for explicit report-only integration.

## Independent scope review

Reviewer: native `hmasd-reviewer` child
`/root/dm_amx_cbsc_continue/cm_am_cbsc_direct_path/rev_ah_cbsc_direct_scope`.
Evidence locator: that child's final answer, headed
“Material finding: orchestration budget breached,” delivered to CM on 2026-09-04.
The exact review finding and disposition are preserved below for recovery without live
agent state. It reviewed the finalized two files in the implementer's isolated tree
`C:/Projects/HMASD-worktrees/impl-cbsc-direct-20260904`; CM copied identical bytes to its
own tree before committing. File SHA-256 comparisons matched between the two trees.

| File | Added physical lines | Scientific-call allowance | Orchestration |
| --- | ---: | ---: | ---: |
| `b1_direct.py` | 85 | 18 | 67 |
| `run_cbsc_omrc_b01_b1_direct.py` | 23 | 0 | 23 |
| Total | 108 | 18 | 90 |

There are zero deleted runtime lines. Tests/docs are excluded from the denominator.
Exact orchestration ranges in the candidate commit: module **1–38, 43–49, 58–59,
66–85**; runner **1–23**. The generous scientific allowance is module **39–42,
50–57, 60–65**, including the entire training-merge comprehension.
Thus **90/108 = 83.33%** is orchestration. Excluding blank lines still gives
**79/97 = 81.44%**. The 2,000-line attempt and 600-line runner limits pass.

Reviewer disposition: return this concrete candidate with the scope blocker; no runtime
or offline profile should be spent on the ineligible source. Further implementation needs
a compliant design or a revised bounded assignment, without denominator padding.
CM accepts this finding and applies the assignment's stop branch.

`scope: none` accurately records that these additions implement none of the engineering
scope specification section 4 machinery: no new supervisor, retry/resume orchestration,
registry, witness, schema validator, or telemetry service. It does **not** mean scope
conformance: the independent section 5 orchestration budget is breached. Existing imported
predicates were not certified; scientific builders were not copied to enlarge the denominator.

## Static data-path assessment and unresolved work

Direct source inspection of existing `b1_engine.py` lines 802–806 and 864–865 confirms
the engine evaluates checkpoint zero and calls `checkpoint_and_evaluate` whenever the
rollout counter reaches a member of `B1_CHECKPOINT_UPDATES`. A single 0-to-48 slice
therefore contains the existing calls at 0, 12, 24, and 48. This is a static observation,
not an executed equivalence or checkpoint test.

Candidate `publish_offline_subset` and runner `main` only wire an offline subset to existing
shared-table, policy-curve/support, training-merge, exact RAW-competence and descriptive
builders. They have not been executed. Unresolved functionality includes:

- learner/request construction and invocation;
- fresh checkpoint policy replay and its complete raw quantities;
- complete checkpoint/exposure and audit projection;
- the three tables `resource_admissions`, `telemetry`, and `audits`;
- complete fifteen-table and summary correctness, required counts, missing-resource handling,
  original identity propagation, and learner-instrumentation coverage;
- direct-route measured cost, toy smoke, focused checks, and real-count r05 publication/readback.

No smoke, test suite, offline r05 publication, heavy profile, learner invocation, or remote
experiment was executed. Only local source/Git inspection, file copying, hashing, and report
production occurred. No runtime failure classification exists. No task handle was handed to
the tracker because none was launched. No actual runtime resource conformance was measured.
The conservative focused/offline test allowance remains **243.55 seconds**, excluding smoke.
The old wrapper's cost envelope is not a measurement of this candidate.

The complete frozen r05 input remains historical engineering input; no record, checkpoint,
identity, receipt, or quarantine was rewritten, resumed, or salvaged. The rejected
`ce94f5afd` implementation was not accepted. No science, RNG, precision, comparator,
interpretive null boundary, lifecycle, or priority change was made.

## Protected-source currentness check

Run in the CM worktree after the candidate commit, the following comparison was silent
and exited 0:

```powershell
git diff --exit-code 1cbad766a973641e3cac2747129621331750b840 -- experiments/candidates/capability_bound_semantic_currentness/omrc_b01 ':!experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_direct.py'
```

A short local byte comparison additionally checked every pre-existing file in that source
directory against the baseline with Git's repository checkout filters applied, so Windows
line-ending conversion is accounted for explicitly:

```python
from pathlib import Path
import subprocess
base = '1cbad766a973641e3cac2747129621331750b840'
prefix = 'experiments/candidates/capability_bound_semantic_currentness/omrc_b01'
paths = subprocess.check_output(
    ['git', 'ls-tree', '-r', '--name-only', base, '--', prefix], text=True
).splitlines()
mismatches = [p for p in paths if subprocess.check_output(
    ['git', 'cat-file', '--filters', base + ':' + p]
) != Path(p).read_bytes()]
print(len(paths), mismatches)
```

Observed result: **37 protected existing files, zero mismatches**, exit 0. This compares
the baseline source surface with the actual working tree, not commit identity. It establishes
no change to these protected files; it does not certify the new caller's runtime semantics.
The candidate's changed-path inventory contains only the two new files named above.

Next step belongs to DM intake: record the bounded engineering stop and choose any subsequent
bounded assignment. This report supplies no scientific polarity and no ready launch SHA.
