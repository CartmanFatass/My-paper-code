# CRTO B08 P70 source technical acceptance

Delivered source-ready B08 implementation, independently reviewed, with no material remaining
source defect identified. Source/check/review commit `9ed83fc06e328fd9ca4e171852f37bdcb0de8d63`
was pushed immediately to `origin/codex/crto`. This record is a source-engineering return to DM
and Root, not a scientific result or allocation. No scientific staging, actual-node admission,
population/label reconstruction, predictor fitting, real gate training, scientific smoke,
result-bearing invocation, retry or Pro Send occurred.

## Assigned boundary and implementation

Authoring checkout: `C:/Projects/HMASD-worktrees/codex-crto`, branch `codex/crto`, clean starting
revision `de14dbab4bde01c3467885c78270ed73888e13fa`. CM owned this checkout's index throughout
the batch. No unrelated change was present or altered. The card remains frozen at accepted
`68044fdcbd77ca8875526b099a01f4bb3f892ece`; Root's P70 source allocation superseded only its
historical zero-implementation statement. DM-owned card/intake/DIRECTION/audit/owner files
were not edited.

Changed runtime paths:
- `experiments/candidates/commitment_residual_triggered_options/native_cost_b08/__init__.py`
- `experiments/candidates/commitment_residual_triggered_options/native_cost_b08/experiment.py`
- `scripts/run_crto_native_cost_b08.py`

The loss detaches native labels, masks the legal maximum and softmax, uses temperature1 and
cost scale .01, sums each row's expected cost, then takes the equal-row mean. All three arms
call the same loss. The unchanged B04 preparation and packet helpers retain the source and
learner namespaces, predictor/calibration laws, selected identities, Sattolo cells and ordinals.
The copied update body retains CPU FP32/thread1, canonical cyclic batch32, common seed0
initialization, fresh Adam, clipping and uninterrupted 258-update trajectories. SHORT33 and
LONG258 snapshots stay in memory; all paths finish before six readouts. Existing recurrent
history collation, 42/52-dimensional inputs, GRU/adapter/head and legal printed-order ties
remain unchanged. No completed helper or result was modified.

New readout publishes all 16 rows per arm/endpoint with masks, native labels, eight logits,
selected/oracle actions and regrets; all signed paired gains/losses are retained for new RAW,
new DERANGED and fixed historical B04 RAW separately. New RAW-LONG competence qualifies both
endpoints. The conjunction uses strict .0025 independently at each endpoint, retains mixed
and adverse readings, and does not select a checkpoint. Historical changes are descriptive.
The native comparison records old/new label differences and old actions rescored on new labels.
Its 1e-7 absolute label tolerance is below the .01 action/.0025 mean scales; changed sign or
margin readings can limit even smaller discrepancies. This is numerical comparison integrity,
not a byte-equality requirement. Damaged endpoint comparisons retain other trustworthy endpoint
facts. Missing RAW-LONG competence is unknown, not observed weakness or negative polarity.
Parent acceptance subsequently found that the adverse list and mixed-budget flag could still
use an untrustworthy negative contrast. The correction filters those interpretations by each
individual contrast's trust flag, retaining all numerical contrasts/rows and any independently
trustworthy loss even when another comparison limits that endpoint. The original source
acceptance is superseded for this corrected reading; no result-bearing work used it.

Wall accounting measures each arm's training/evaluation/scoring intervals and charges every
arm all remaining shared time. The monitor includes accrued common time, checks during work
and around publication, and raises on cap breach. The inner summary timestamp explicitly says
pre-publication. After the required run command terminates, `account` reduces its actual terminal
supervisor elapsed into `complete_accounting.json`: shared wall minus all arm intervals gives
shared overhead, charged in full to each arm. That collection reduction preserves `summary.json`.
It reports cap breaches and never sums arm charges as machine time. Interpreter startup and
shutdown are covered by the outer measurement; the inner timestamp alone cannot establish
complete conformance. A callback monitor is not a preemptive operating-system deadline.

Scope-spec Â§4 additions: **none**, per card Â§7. Tool-counted new non-test runtime lines: module315
+ initializer1 + runner43 = **359**, within 2,000; runner43 within600. No generic execution,
retry, provenance guard, telemetry service or framework was added. Required publication and
wall bookkeeping were reviewed for purpose; no ratio gate or line-by-line census was introduced.

## Focused acceptance evidence

Independent review: [P70 review](CRTO_NATIVE_COST_B08_P70_REVIEW_20260908.md), including follow-up
inspection of endpoint-local limitation and unknown RAW competence. No material finding remains.
Reviewer inspected source, direct dependencies, historical JSON and tests; it did not rerun fixtures.
CM inspected the complete staged runtime diff, tests and review. `git diff --cached --check` passed.

Interpreter: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.
Working directory: `C:/Projects/HMASD-worktrees/codex-crto`.
Base fixture command (run tags below are invocation-owned):

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/commitment_residual_triggered_options/test/b08-p70-20260909-c tests/experiments/candidates/commitment_residual_triggered_options/native_cost_b08
```

| Invocation | Check/result | Pytest wall | Process wall |
| --- | --- | ---: | ---: |
| `b08-p70-20260909-a` | 11 passed; 2 fixture setup errors because scratch parent was absent | 2.08s | 3.108s |
| `b08-p70-20260909-b` | Parent directory created; all 13 passed | 1.98s | 3.093s |
| `b08-p70-20260909-c` | Endpoint-local incomplete comparison correction; all 13 passed | 2.16s | 3.329s |
| `b08-p70-20260909-d` | Only `test_native_cost.py::test_historical_floor_and_weak_new_raw_cannot_be_rescued`, after unknown-competence correction; 1 passed | 1.95s | 3.099s |
| `b08-p70-20260909-e` | `test_adverse_and_mixed_reading_requires_individual_contrast_trust` and existing `test_mixed_budget_preserves_losses_and_no_best_endpoint`; 2 passed | 1.93s | 3.102s |

Total reported fixture wall **10.10s**; total command process wall **15.731s**, below300s.
Tests cover independently calculated equal-row masked loss/gradients, detached labels, unequal
legal-set sizes, extreme logits, single legal actions, zero illegal gradients, printed ties,
competence limits, all three strict thresholds, historical floor, weak/unknown RAW, signed
losses and mixed endpoints, historical disagreement, shared/per-arm accounting and breach,
JSON publication/readback and mocked assembly ordering. The assembly replaces all preparation,
real learner and forward entry points; no scientific model or host was run. Existing B04
host/RNG helpers were reused and inspected, not rerun as a historical reconstruction or smoke.

Automatic tool review rejected recursive scratch deletion (generic `blocked by policy`). CM
used scoped deletion of the known fixture files followed by empty directories. `Test-Path`
confirmed all five invocation roots absent. Invocations a/d/e created no scratch root.
No evidence root or another invocation's files were removed. Test failure diagnostics above
were retained before cleanup.

## Literal prospective execution binding â€” not staged or executed

- Source/launch SHA: `9ed83fc06e328fd9ca4e171852f37bdcb0de8d63` (all runtime paths and unchanged
  dependencies at that commit). This later documentation-only record does not change that surface.
- Card: `docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_SCIENCE_CARD_20260908.md`
  at `68044fdcbd77ca8875526b099a01f4bb3f892ece`, Git-blob SHA256
  `43268365b5c887d2b75f3e6945cec3eeb03a2d1b2fed0f4f730311a0cb55fae7`.
- Historical input: `docs/research/candidates/commitment_residual_triggered_options/CRTO_RESIDUAL_CYCLE_ENDPOINTS_B04_RESULT_20260904.json`
  at `c9690db8ef340ac8201043183a864454f08c0431`, exact Git-blob193466 bytes, SHA256
  `1e5bd64d9f93ec75d5fe27921ac5c7877c4f027b5f01e239cf691c9e0ad4716a`.
  The current Git blob equals these frozen bytes. The Windows working copy differs only by
  CRLF; parsed JSON equals the frozen input. Future evidence staging must use the declared
  Git-blob bytes at this digest, not the CRLF working-copy bytes.
- Prospective staged input path:
  `/home/wu/hmasd-inputs/crto-b08-p70/CRTO_RESIDUAL_CYCLE_ENDPOINTS_B04_RESULT_20260904.json`.
- Node `wsl_4070`, SSH `hmasd-wsl-node`, host `LAPTOP-U9TDKC8A`, Ubuntu24.04 WSL2;
  Python `/home/wu/.venvs/hmasd/bin/python` (configured3.10.21, torch2.7.0+cu118, NumPy1.26.3).
  Execution remains CPU FP32/thread1. Host identity is not the estimand; only the card/AGENTS
  prospective portability fallback is available, with no accepted remote process duplicated.
- Prospective detached cwd:
  `/home/wu/hmasd-worktrees/crto-b08-p70-9ed83fc06e328fd9ca4e171852f37bdcb0de8d63`.
- Prospective result root:
  `/home/wu/projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/b08_seed0_p70_20260909`.
- Prospective supervisor handle `crto-b08-p70-seed0-20260909`; `/usr/local/bin/agent-task`.
  No handle is accepted and no process exists under this assignment.

Exact prospective supervisor invocation, issued on the declared node only after Root's actual
result-bearing allocation and exact-source/input staging:

```bash
/usr/local/bin/agent-task run crto-b08-p70-seed0-20260909 'cd /home/wu/hmasd-worktrees/crto-b08-p70-9ed83fc06e328fd9ca4e171852f37bdcb0de8d63 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/b08_seed0_p70_20260909/admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_crto_native_cost_b08.py run --seed 0 --historical-summary /home/wu/hmasd-inputs/crto-b08-p70/CRTO_RESIDUAL_CYCLE_ENDPOINTS_B04_RESULT_20260904.json --output-dir /home/wu/projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/b08_seed0_p70_20260909 --execution-node wsl_4070'
```

This is one admitted seed0 package, three arms,258 updates each, endpoints33/258, no retries,
resume, GPU, fourth arm or automatic successor. Actual-node physical/effective available memory
must each be >=4GiB immediately before the runner. Caps:1200s per conservatively charged arm,
1500s complete shared command. A breach is reported and does not allocate more work. The
supervisor elapsed used for collection includes the whole quoted command, conservatively
including admission and shell startup, and final scientific summary publication/shutdown.
The collector supplies that measured number to the same runner's `account --output-dir` and
`--complete-wall-seconds` arguments, retains the terminal supervisor source, and inspects both
summary and final accounting. The post-terminal reduction is collection metadata, separately
outside the measured scientific command, not a second learner invocation.

Per-arm cost projection: reused card/P68 measured B04 law `3*(S+258*t_j+E_j+Q)` gives RAW
413.97090837899304s, TRUE411.96144017999904s, DERANGED413.06858835300955s; shared complete-work
planning estimate515.3820955440096s. These fit the prospective caps. Setup/publication/new-loss
and current-load overhead remain unmeasured. Do not sum the arm projections; one sequential
logical invocation makes study critical path equal summed invocation wall, while aggregate CPU
is unmeasured. Historical171.8017914000011s was pre-publication, not complete wall.

Post-learner coverage: the new scorer and actual JSON publisher/account reducer passed synthetic
16-row fixture readback, including the historical comparison structure; full assembly was checked
with preparation/learner/forward replaced. This establishes publication wiring and arithmetic,
not empirical output, actual historical label agreement, actual counts, resource conformance or
scientific truth. No real scientific smoke is implied or required by this source-only return.

Next owner: DM accepts this technical batch; Root decides actual runtime allocation and names
one observer for the exact accepted handle through collection. Those execution/staging/admission/
observation facts remain unperformed. CM's assigned P70 source batch stops here.
