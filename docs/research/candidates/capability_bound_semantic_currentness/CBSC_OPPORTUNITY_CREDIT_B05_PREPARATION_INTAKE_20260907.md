# CBSC B05 / P18 preparation intake

**SOURCE_REPAIR_NEEDED.** The prospective B05 question, seed 21223, shared
prepared runtime, prediction, exposure and costs are committed. The accepted
source cannot express that seed or truthful B05 artifact identity, so no runnable
literal or execution allocation is ready. This is a source-inspection finding,
not an attempted or adverse B result.

## Inputs, checks and reading

P18 authority is `80dd2af11d204ef6f57dd9aed98dc5558f69c801`. The [B05 card](CBSC_OPPORTUNITY_CREDIT_B05_SCIENCE_CARD_20260907.md)
and [machine counts/exposure](CBSC_OPPORTUNITY_CREDIT_B05_EXPOSURE_AND_COST_20260907.json)
were committed prospectively at `a213567ce576ba836427b8490f183120b9de23e6`.
Same CM's complete [source-gap handoff](CBSC_OPPORTUNITY_CREDIT_B05_ROOT_HANDOFF_20260907.md)
is `2d0f95f091e0f92394bd08535fba62566e9ecb30`. Authoring checkout remains
`C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`, branch `codex/cbsc`.

P18 rule applied verbatim:

> Record any source incompatibility
> as a precise bounded CM repair need; do not silently change semantics.

I read the entire CM handoff, its one-path diff and the actual affected source
boundaries. CM's static comparison found no difference from accepted scientific
source `a3c2a49bf7002639d43a94f460b688d50c6c42dd` in the runner or complete
`opportunity_credit_b04/` and `omrc_b01/` surfaces. I inspected the CLI guard,
`expected_seed`, `run_arm`, `OBJECT`, summary/pair construction and snapshot
payload. Source inspection and stdlib AST/arithmetic are the evidence path;
neither CM nor DM imported the scientific module, ran --help/tests, staged a
remote checkout, admitted resources or executed a candidate.

## Direct source findings and their limit

1. `scripts/run_cbsc_opportunity_credit_b04.py:30` compares the requested seed
   with `expected_seed(args.engineering)` before accepting the CLI arguments.
2. `opportunity_credit_b04/run.py:28` returns engineering seed 21211 or formal
   seed 21217. Its independent `run_arm` check at line108 rejects a different
   seed. The function creates the output directory and sets Torch threads before
   that check; direct invocation was not used as a bypass or probe.
3. `opportunity_credit_b04/learner.py:17` defines the fixed B04 `OBJECT` string.
   The runner console, arm summary, paired summary and
   `opportunity_credit_b04/snapshot.py:24` consume that identity. Actual seed and
   new output paths alone do not replace those fixed object fields with B05.

The inference is narrowly determined by these inspected branches: an unchanged
source invocation requesting formal seed 21223 cannot pass both guards. No
actual parser exception or runtime failure is claimed from this read-only work.
The B1_RUN RNG namespace is intentionally preserved scientific addressing; it
is not an object-label defect. Existing thread/dtype/device metadata remains,
while executable/version provenance currently comes from the exact command and
P17 metadata rather than a fresh import or an internal interpreter field.

Strongest support for the disposition is the two explicit guards plus shared
identity consumers. The strongest positive counterpoint is P17's real complete
installation/import/readback success; that prepared environment remains valid.
It does not make the selected B05 seed reachable through the inspected source.
No old runtime cause, algorithm failure or direction polarity follows.

## Prospective quantities and preserved science

One fresh paired seed 21223; both RAW and STRUCT in
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`,
observed CPython 3.12.3 / NumPy 1.26.3 / Torch 2.7.0+cu118, CPU FP32 and one
Torch thread. The B04 sampled decision-plus-settlement target, rollout
normalization, decision-only value loss, full recurrent BPTT, public adapters,
native objective, REQUEST_ONLY context and final-update48 comparison are unchanged.
Old B04 RAW 12.0375 versus REQUEST_ONLY 12.375 remains separate, with its original
missing STRUCT and runtime binding. No historical value is the new pair's control.

Machine arithmetic gives 2 arms x 1 seed x 48 rollouts x 8 episodes,
1536 Adam steps, 128 evaluation executions and 136192 train/evaluation transitions;
RAW's rules add 96 existing-tape passes / 2304 action scores once. The original
per-arm cost law includes bootstrap/admission, host, all training/evaluation,
snapshots, context, publication/readback, pairing and finish. Old same-arm timing
scenarios are RAW 159.38 s and STRUCT 181.56 s; both fall below requested 600 s
complete per-arm caps, 1200 s summed. They are not new-runtime timing evidence.
The same-learner B04 RAW displacement of 12.2054702557% supplies prior movement
evidence, not a forecast of B05 performance. New actual exposure is zero for
acquisition, installation, target import/probe, host/model, optimizer and evaluation.

MEI remains 0.25 native return; tuned same-information/upper headroom is absent.
The prelaunch prediction of a mean gap inside [-0.25,+0.25] is **not yet scorable**.
Owner prediction: **not taken (unattended)**. No B outcome or consumption state
exists. DIRECTION and Portfolio science, lifecycle, priority, recast count and
UAV-entry status are unchanged. No new mechanism or comparator class required
fresh literature retrieval for this source/identity finding.

## Decisions this intake produces

1. **Object / technical:** (a) accept the precise SOURCE_REPAIR_NEEDED finding;
   (b) present an unchanged-source literal as executable; (c) test the known
   rejection with an unallocated runtime call. Recommend/select **(a)**.
2. **Object / next-task recommendation:** (a) return a bounded fresh-seed/object
   correction request while retaining the prospective card; (b) substitute old
   seed 21217 or old RAW; (c) add an acquisition/import/cause series. Recommend/
   select **(a)**. No implementation or experiment is dispatched by this intake.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a) for each decision.
Both records are reversible; owner flags none. The new-card P2 is
`20260907-cbsc-007`. Owner reviews returned [] at card freeze and intake, with
no relevant audit override. The [Chinese preparation brief](../../portfolio/owner/briefs/capability_bound_semantic_currentness/2026-09-07_B05_PREPARATION.md)
describes the zero-execution source finding. This is preparation of a B card,
not a valid B performance result or a new engineering invocation.

## Exact missing task and return route

Through Root to Portfolio, request one bounded CM correction enabling selected
B05 seed 21223 and consistent B05 identity through the CLI, arm, summary, snapshot
and pair, while preserving B04 formal seed 21217 / engineering seed 21211 and old
profile behavior. The concrete surfaces are the runner plus
`opportunity_credit_b04/{run.py,learner.py,snapshot.py}`; a thin B05 entry/profile
may be the implementation choice. No `omrc_b01/` numerical, host, adapter or RNG
change is justified by this finding. Do not globally rename old artifacts,
monkeypatch a live invocation or add a profile registry/framework.

The correction's acceptance must show seed 21223 reaching both arms' host, model,
action-uniform and minibatch addressing; truthful matching B05 metadata; unchanged
learner/exposure and primary pairing; retained RAW rule reuse; and preserved
B04 behavior. Use focused checks proportional to that change within the existing
account; no automatic real-learner smoke or historical replay follows. No source
is accepted merely because its argument parser returns success.

Then bind the actual corrected full SHA, unchanged preflight provenance, prepared
interpreter, requested fresh B05 cwd/outputs/handles, complete per-arm deadline
and admission/log/collection literals. Full source and execution acceptance remain
open facts, not supplied by the current prospective names. After a future explicit
allocation, the ordered route is RAW -> CM terminal/primary/seed/runtime/count
acceptance -> STRUCT irrespective of RAW score -> complete pair publication inside
STRUCT's cap -> DM intake. Preserve every outcome and stop dependent work only
for the card's actual integrity/admission/cap conditions.

This return supplies the exact next-task need. It authorizes no source change,
dependency work, learner call or retry. There is no live run, accepted supervisor
handle, pending collection or Pro request to observe at this boundary.
