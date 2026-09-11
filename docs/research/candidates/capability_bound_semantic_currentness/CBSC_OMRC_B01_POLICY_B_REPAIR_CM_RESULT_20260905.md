# CBSC B1 policy B repair: CM result

Date: 2026-09-05. **Whole-change candidate assessed; source unaccepted.**
Engineering evidence only, with no scientific polarity or runtime acceptance.

The attempted execution-to-publication repair adds **165** non-test source lines,
exceeding policy B's whole-change cap by **65**. Independent review also identifies
a material missingness-propagation defect: an incomplete resource observation can still
produce a positive mechanical resource/conformance certificate. CM returns this exact
candidate without another implementation iteration or runtime invocation. Neither finding
proves every possible repair infeasible, and this is not a completed-correct-repair claim.

## Contract, baseline and recoverable commits

Full frozen contract: `CBSC_OMRC_B01_POLICY_B_REPAIR_SELECTION_INTAKE_20260905.md`
at `e71d9b5be00963d5258cabfe84ef6b2d7a0067b1`. Accepted baseline for the entire logical
change: `0ffca930b9e43b0c6402fce65493cdf6ae24f66f`. All additions/deletions below are
measured from that baseline across all six files, not reset at a follow-up commit.

CM source preservation commit: **`9ee4a381f9d486276dcdd66e69b27d5a4b3cb413`**.
Branch/upstream: `codex/cm-cbsc-policy-b-20260905` /
`origin/codex/cm-cbsc-policy-b-20260905`.
Tree: `C:/Projects/HMASD-worktrees/cm-cbsc-policy-b-20260905`.

Implementer preservation commit: **`cfbe91367fd56f9d4bd4ace3cbe5c8123fddd4af`**.
Branch/upstream: `impl-cbsc-policy-b-map-20260905` /
`origin/impl-cbsc-policy-b-map-20260905`.
Tree: `C:/Projects/HMASD-worktrees/impl-cbsc-policy-b-map-20260905`.

CM committed only explicit owned paths and immediately pushed both branches. Both pushes
succeeded. Before writing this report both trees had empty `git status --short`, and each
HEAD equaled its upstream. The six candidate working files matched byte-for-byte between
trees. Neither source commit is for integration or launch. This report is delivered in a
separate docs-only commit for explicit report-only integration.

No earlier rejected source was accepted or cherry-picked. Prior trees, saved-project dirty
work and r01-r07 evidence remain untouched. No attempt was resumed, salvaged or relabelled.

## Actual full scope accounting and review

Independent reviewer: native `hmasd-reviewer`
`/root/dm_amx_cbsc_continue/cm_am_cbsc_direct_path/rev_ah_cbsc_direct_scope`.
Evidence locator: its final 2026-09-05 answer beginning “Reviewed the whole attempted
repair,” identifying implementer commit `cfbe91367fd56f9d4bd4ace3cbe5c8123fddd4af`.
The complete material findings and accounting are preserved here for recovery without
the live native-agent conversation.

All files are under `experiments/candidates/capability_bound_semantic_currentness/omrc_b01/`.
A is added source lines, D deleted source lines, and O changed lines classified as
orchestration. Replacements count on both sides. Tests and documents are excluded.

| File | A | D | Generous computational allowance | O |
| --- | ---: | ---: | ---: | ---: |
| `b1.py` | 47 | 182 | 0 | 229 |
| `b1_mechanical.py` | 4 | 3 | 7 | 0 |
| `b1_metrics_artifact.py` | 7 | 70 | 18 | 59 |
| `b1_metrics_production.py` | 46 | 139 | 30 | 155 |
| `b1_metrics_training_assembly.py` | 2 | 27 | 0 | 29 |
| `telemetry.py` | 59 | 5 | 0 | 64 |
| **Total** | **165** | **426** | **55** | **536** |

Exact defensible classification: every added/deleted line in this baseline diff is
orchestration **except** the following deliberately generous computational allowances.
Old numbers address baseline files; new numbers address either candidate source commit:

- Mechanical: old **933–934, 940**; new **640–643**.
- Artifact: old **1428–1430, 1442, 1773–1776, 1785–1793**; new **1424**.
- Production: old **1909–1913, 1931–1948, 1955–1959, 2005**; new **1912**.

Resource measurement/aggregation is orchestration. No unchanged helper is counted.
Thus **O/(A+D) = 536/591 = 90.69%**. Net deletion alone does not qualify the exception:
**A=165>100**, so this candidate is outside policy B and also fails the ordinary ratio
limit. The 2,000-added-line limit passes; the existing runner is unchanged. Tests: **A=0,
D=0**. Source commits contain no docs; this standalone result document is reported separately
by its docs-only Git commit, not included in A/D/O.

The actual additions serve both supervisors' independent wall handling (within the 47
`b1.py` additions), scoped incomplete/partial telemetry handling (59 in `telemetry.py`),
optional replay/training measurement and metadata publication (46 production, 2 training),
mechanical resource handling (4), and descriptive/resource summary and cap changes (7 artifact).
These name the required responsibilities that drove the **65-line excess** in this candidate;
they do not establish that all 165 lines are irreducible.

No copied scientific padding, relocation or new section-4 machinery was identified by the
reviewer. `scope: none` means no new supervisor framework, registry, witness, retry/lease,
validator layer or resource service; it is not a claim of budget or correctness conformance.
Explicit B1 options retain strict default behavior for the pre-existing B0 callers.

## Material static defect: lost incomplete status in mechanical projection

The exact reachable data-flow described by independent review is:

1. Successful resource samples followed by a sampler error leave true, nonnull observed
   values. `telemetry.py:631–640` sets `measurement_complete=False` while preserving these
   observations; B1 normalization also sets `resources_unmeasured=True`.
2. `b1_metrics_training_assembly.py:722–730` copies the resource numbers into mechanical
   facts but omits both `measurement_complete` and `resources_unmeasured`.
3. `b1_mechanical.py:640–650` detects unknown observations only through null resource
   numbers. Previously observed values below the limits therefore permit `resource_caps=True`.
4. At `b1_mechanical.py:945`, other passing components can consequently produce
   `mechanical_conformance_pass=True` despite incomplete observation.

The missingness flag is **not erased from every output**: the telemetry measurement retains
it, and `build_result_rule_summary` aggregates it into the summary. It is lost specifically
at the projection to mechanical resource facts, making those certificates inconsistent with
the telemetry/summary. This violates the frozen prohibition on false resource/conformance
certification. Correct handling would preserve incomplete status through that projection while
retaining available measurements. No such follow-up repair was made in this bounded return.

This is a static correctness finding, not a reproduced runtime failure or a classification of
the unique historical r07 sampler cause. No runtime counterexample was executed.

## Separate unresolved portability dependency

Read-only inspection of frozen r05 slot-00 admission metadata found this original path:

`C:/Projects/HMASD/temp/directions/capability_bound_semantic_currentness/exp/pub_r05/policy-replay/00/.admission.json.raw-d763258b5e7147c1abfdde0e7564d6ca.json`

The original local file exists; `snap_r05/policy-replay/00` also contains the same basename.
There is **no missing-local-file claim**. Candidate production lines **355–358 and 436–442**
still resolve the admission's original absolute path. Portable execution against the separately
staged remote fixture therefore remains an unresolved dependency. No historical paths, IDs,
bytes or outcomes were rewritten or used to select the repair, and no remote probe was run.

## Structural coverage, protected source and verification limits

Direct inspection finds the initial fifteen-table construction, original RAW competence,
descriptive curves, literal-null interpretations, child-result/count checks, admission and
independent wall checks structurally retained. The change removes duplicate consumer
reconstruction and selected source/resource refusals. Rehydrate is unchanged: actual tape,
configuration and count checks remain. This is source-review evidence only, not complete
measurement preservation, publication compatibility or runtime acceptance.

The complete four-arm/three-seed B1 assignment remains the contract: 384 episodes, 48 updates,
768 Adam steps per slot; CPU FP32, original RNG/PPO, checkpoints 0/12/24/48 and original held-out
evaluation and interpretation boundaries. No scientific launch or claimed change to this meaning
was made. B0 retains default strict telemetry behavior structurally; no runtime equivalence was run.

CM's local protected-source check enumerated baseline `omrc_b01` files plus the existing B1
runner using `git ls-tree -r --name-only 0ffca930b -- <paths>`, excluding the six owned changed
files. For each remaining file, it compared `git cat-file --filters <baseline>:<path>` bytes
with `Path(path).read_bytes()`, explicitly accounting for Git's Windows checkout filters.
Observed: **32 protected files, zero byte mismatches**, exit zero. Comparing all six changed
files to the implementer tree likewise found **zero byte mismatches**. CM inspected their full
diff; `git diff --check` passed. Implementer AST parsing passed without importing the modules.

No smoke, focused test, learner, replay execution, r05 offline publication, resource receipt,
remote verification or r08 was run. No experiment handle exists and no tracker adoption was
needed. No measured runtime/cost/resource claim is available; the previous 243.55-second
focused/offline allowance remains unspent by this change. Full real-constant offline publication
and readback of every table plus summary remain unverified. Root integration-before-verification
was respected by making no verification invocation.

CM disposition: return the whole-change candidate as **unaccepted** for both the additions
breach and the static missingness defect, with the separate portability dependency recorded.
No further implementation loop, tests or source integration are proposed by this result.
