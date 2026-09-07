# Service-allocation completion: technical source acceptance, 2026-09-07

P08-VSPC1-COMPLETE-01 implements the selected publication dependency repair. This record
accepts source/fixture/review conformance only. **No rule completion invocation occurred.**
The original GENERIC exit 1 and learner-only evidence remain unchanged.

## Contract and source ownership

Authority is [amendment intake §§2–3](VSPC1_K4_SERVICE_ALLOCATION_COMPLETION_AMENDMENT_INTAKE_20260907.md),
formed response `99151a4a0f2da264a2c13695591a56867e1add3c` §§II–IV and the
[five-item handoff](pro_packets/20260907_service_allocation_completion_amendment/CM_REPAIR_HANDOFF.md).
Root's P08 release supersedes prepared-only wording; current AGENTS §6 supersedes the old
isolated-branch wording. CM reused the sole authoring checkout
`C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch `codex/direction-vsp_c1`,
clean at `70b419a2ba29a1b912d438c1301f8a9543faf42b`. CM was the sole editing owner;
independent review was read-only. No new branch/worktree or unrelated edit was made.

Owned changes are reporting.py, the new scripts/complete_vspc1_k4_service_allocation_b01.py,
and the existing publication fixture in tests/experiments/candidates/vsp_c1/
k4_service_allocation_b01/test_contract.py. Direct Git diff confirms experiment.py and the
original learner runner unchanged. Original remote/local learner summaries were not modified.
Engineering scope §4 additions: **none**, per selected handoff §5 and formed response §IV.

## Implementation and affected boundaries

`compare()` copies each budget and converts only a list/tuple checkpoints field to tuple.
It neither sorts nor drops fields nor changes numeric values. Existing full-budget equality
continues to reject different seeds, updates, train/eval sizes, checkpoint values/order or
other unequal fields; arm ordering remains checked. Caller-owned budgets are untouched.
Contrast, conditional SE, five-point AUC, initial-change and rule-relative arithmetic have
no source change. This repairs the loaded FACTOR/native GENERIC representation boundary.

The new entry accepts --factor-summary, --generic-summary, --out and fixed --seed 402.
It reads the two saved JSON summaries, obtains launch metadata, and calls only existing
`evaluate_rule(Budget(seed=args.seed))` once. Four native thread environment limits and
Torch compute/inter-op limits are set to one. The unchanged evaluation uses CPU float32
state/segment tensors, periods (2,6), 128 episodes per period, evaluation namespaces31/32,
update0 and the existing batch shapes/order. Each rule trajectory starts its own queues/h.
Import defines model classes but the entry instantiates no model, optimizer or learner;
there is no run(), learner reevaluation, --describe or training RNG call.

The completed rule is written/read as new-root summary.json before paired publication,
so a later paired-output failure leaves the rule summary. Both outputs carry explicit
outcome-informed completion metadata, original learner-source SHA, readonly input paths,
original GENERIC exit1 and new source/host/interpreter/argv versions. Launch metadata is
read before rule evaluation. The entry writes the three existing contrasts and original
curves through the unchanged arithmetic, then wall/RSS metadata and stdout. It does not
backfill original GENERIC RSS or overwrite original learner outputs.

A later execution assignment must bind the exact readonly original inputs, separate output
root, remote source/cwd/handle and adjacent >=4GiB memory admission within the complete120s
cap. These external frozen bindings are not replaced by a new internal validator/guard.

## Sole focused fixture and direct evidence

Exactly one selected invocation ran locally, bounded by subprocess timeout300s:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_c1/test/service_allocation_completion_20260907/pytest tests/experiments/candidates/vsp_c1/k4_service_allocation_b01/test_contract.py::test_primary_publication_three_contrasts_auc_initial_and_missing_rule
```

Result: **1 passed in5.07s; complete subprocess wall6.915941299987026s**. The cache_dir
warning arises with cacheprovider disabled; it does not affect the assertions. No old
nine-test suite or full-runner smoke was run. The fixture has exactly three publication cases:

1. Full synthetic budget including (0,64,128,192,256); FACTOR JSON-loaded/list and GENERIC
   native/tuple; learner-only publication succeeds.
2. Add the literal synthetic rule and write/read all three correlated contrasts; retained
   checks cover Delta, per-period paired SE, E_F-E_G=Delta, five-point AUC, initial changes,
   rule-relative initial values and endpoint/curve preservation.
3. A real checkpoint order difference (0,64,192,128,256) raises the existing budget error.

Inputs use literal values and ordinary arrays/statistics. Existing pure endpoint formatting
helpers are called; no model, optimizer, environment, rule evaluator or scientific RNG is
called. No formal seed402 tape or learned-policy evaluation occurred. The fixture uses
synthetic seed9402 labels only. Review/static reads add no scientific execution exposure.

Saved invocation JSON/log and synthetic pair files are under this authoring checkout's
`temp/directions/vsp_c1/test/service_allocation_completion_20260907/`.
`pytest/test_primary_publication_three0/pair_without_rule.json` reads learner_contrast_only;
`pair.json` reads complete and contains FACTOR-GENERIC, FACTOR-LQ-EXCLUDE and
GENERIC-LQ-EXCLUDE. Both retain descriptive AUC delta0.07843750000000005 from synthetic
values, not a measured B result. CM directly inspected these artifacts; no repeat invocation.

## Independent review and budgets

The reused independent reviewer read the actual source diff, selected contract, fixture
and saved outputs without editing or executing tests/scientific code. It found no material
issue: checkpoint normalization preserves real mismatches and input ownership; completion
has no learner path; arithmetic and protected source are unchanged; publication preserves
standalone rule data and outcome-informed provenance. The reviewer separately confirmed the final69-line entry after the metadata-ordering
change: launch metadata precedes sole rule evaluation, standalone rule output precedes paired
output, scientific behavior unchanged, no material finding. No additional fixture ran.

Non-test source change: reporting A5/D1 plus completion entry A69/D0 = **A74/D1, A+D75**,
below150. Entry length69 is below100. Fixture change A9/D3; this technical record is separate
documentation. No orchestration framework or §4 machinery was introduced. The thin entry's
I/O/metadata is necessary to the selected one-call completion; no ratio-based refusal applies.

## Technical conclusion and remaining owner

The exact publication defect has focused synthetic coverage and independent read-only review.
This establishes source/fixture conformance, not empirical completion or a measured rule value.
Per selected counts, a future successful sole rule call would add256 episodes/12288ticks/
4096renewals and zero models/updates/Q scores; actual addition at this boundary is zero.
New-host completion unit time remains unknown;120s is the separate complete-call cap, not a
forecast or leftover old budget. No cost probe or rule call was performed.

Return pushed source and technical commits to Root for integration. DM then binds the separately
authorized sole rule completion under the amendment; this CM assignment stops here. No
retraining, learner reevaluation, retry, Pro action or empirical invocation is authorized here.


Accepted source/test commit: **0cd770070675b2be291c8eb37aa57e1f092f5fe2**, immediately
pushed to origin/codex/direction-vsp_c1. Git reports83 additions/4 deletions including tests;
non-test totals remain74 additions/1 deletion. The technical record is committed separately
on its descendant. No source changes followed independent review or the final ordering read.
