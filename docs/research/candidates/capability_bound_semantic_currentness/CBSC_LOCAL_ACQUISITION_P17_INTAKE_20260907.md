# CBSC P17 local acquisition — DM intake

**Decision: accept PATH_PREPARED at the A/RECON metadata-path ceiling.** The one
allocated invocation acquired and transferred both complete cp312 wheels, created
the fresh pinned environment, imported NumPy/Torch, and published/read back the
required metadata. Local and remote terminal exits are zero. Independent outer
command wall is 174.5612299 s, below the complete 600 s cap. No learner ran.

This meets the prospective absolute MEI of one metadata-ready environment. It
does not establish B04 execution, identify an old runtime fault, measure a
currentness effect or change direction lifecycle. The selected next-task need
is a fresh same-runtime paired B preparation, specified below, not another
acquisition or an automatic continuation of the old B04 invocation allowance.

## What I checked and rule applied

I read the complete [CM E0](CBSC_LOCAL_ACQUISITION_P17_RESULT_EVIDENCE_20260907.md)
at `c262eda594348d62bd21d0f0c3753269157e2f1a`, integrated on main as
`07ba3808b5e6c4b426f640b386d21f285db344c6`, against the [card's prospective reading
and P17 allocation](CBSC_LOCAL_ACQUISITION_P16_SCIENCE_CARD_20260907.md#prospective-execution-request-after-code-intake).
P17 authority is `a787ff12cd0212b9fd23d9d861d5d192186028fe`; the prospective
allocation/prediction was committed before launch at
`e612ccbd1889e5dcf5ab0c587c0000266fe60a5f`.

Command source remains `5828af584c5f5e6764f5a44c9951473d82bf04ad`, the exact
literal is bound at `35a4fcaeabb8f8590ac0ac4a410327414bc4ef63`, and preflight
source remains `ec8866b3968fcb1566976ce405d7c552d4d9a5de`. I checked the actual
hidden-launch wrapper, terminal witness, controller and worker JSON, collected
remote supervisor/terminal/admission/install records, local and remote primary
JSON, and the two local file sizes against remote inventory and fixed inputs.
No CM command, import, test, admission or scientific invocation was repeated.

Rule applied verbatim:

> Prospective reading: `PATH_PREPARED` requires observed successful local terminal
> exit and remote terminal exit, complete primary metadata publication/readback with
> `metadata_matches=true`, and the actual complete invocation within 600 s. A ready
> flag, file, test result or SSH success alone is insufficient. `PATH_INCOMPLETE`
> records failure, timeout, missing/mismatching primary metadata, uncertain terminal
> completion or cap breach, while retaining independently observed narrower facts.

Stdlib analysis over the recorded JSON and AST-parsed fixed inputs confirmed the
quoted rule, 23 matching pins, matching local/remote primary mappings, the two
body sizes, 21 named retained links, all terminal checks and both memory floors.
The independent empirical unit is this one complete acquisition/setup invocation.
Its two requests, phases, files and 23 packages are not independent runtime trials.
There is no statistical uncertainty estimate or stable-success claim from one run.

## Direct observation, counts and receipts

| Quantity | Observed result |
| --- | --- |
| Complete controller wall from its original origin through publication | 174.35900000005495 s |
| Independent stopwatch around the exact literal, including startup/teardown | 174.5612299 s |
| Local / remote terminal exit | 0 / 0; remote supervisor finished, tmux inactive |
| New Torch / Triton body length on each node | 955455844 / 156503769 bytes |
| Acquired body payload / acquisition plus transfer payload | 1111959613 / 2223919226 bytes, before protocol overhead |
| Retained input containers / pinned versions / fresh venvs | 21 / 23 / 1 |
| Full-body GETs / two-file transfer / offline install / metadata process | 2 / 1 / 1 / 1 |
| Local / remote available physical and effective memory at admission | 7191392256 / 15647854592 bytes; both above 4294967296 |
| Host episodes / model calls / optimizer steps / policy evaluations | 0 / 0 / 0 / 0 |

Operation counts follow the bound execution path and successful retained
artifacts; they are not packet-capture measurements. The worker's 174.328 s and
the supervisor's 8 s describe subsets. Neither is substituted for the complete
invocation. The successful chain finished before the original 540 s work cutoff
and 600 s cap. The remaining 425.4387701 s is unused allowance, not another run.

The fresh prefix is
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907`.
Its recorded lexical executable is that prefix's `bin/python`, resolved/base
executable `/usr/bin/python3.12`, with CPython 3.12.3, NumPy 1.26.3,
Torch 2.7.0+cu118 and CUDA build 11.8. All 23 distribution versions and the
NumPy/Torch module locations match the primary contract. No GPU kernel, B04
tape constructor, model, optimizer or evaluator was exercised.

Hidden wrapper PID 10696 started at `2026-09-08T02:46:39.3752536Z`; controller
PID 28812 started at `2026-09-08T02:46:40.334933Z`. The independent exact-command
stopwatch started at `2026-09-08T02:46:40.2322180Z`, and its terminal witness
ended at `2026-09-08T02:49:34.8247584Z`. The remote setup handle is
`cbsc-local-acquisition-p16-20260907`, supervisor PID 2755729. Root adopted
observation; CM collected terminal facts without relaunching that identity.

Raw receipts are retained in the authoring checkout
`C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906` under
`temp/directions/capability_bound_semantic_currentness/exp/`:

- `local_acquisition_p17_launch_receipt.json`, `local_acquisition_p17_launch.ps1`,
  `local_acquisition_p17_controller_identity.json` and `local_acquisition_p17_terminal.json`;
- `local_acquisition_p16_20260907/{command_result.json,worker_result.json,admission.json,summary.json}`,
  complete wheels and existing phase logs;
- `local_acquisition_p17_remote_collection.json`, containing remote primary,
  terminal, supervisor, admission, install and wheel-inventory records;
- `local_acquisition_p17_dm_intake_counts.json`, the bounded recorded-data check
  and arithmetic used in this intake.

Remote outputs remain under the exact-source checkout
`/home/wu/hmasd-worktrees/cbsc-local-acquisition-p16-20260907/` at the same
`temp/directions/capability_bound_semantic_currentness/exp/local_acquisition_p16_20260907`
relative path. Full launch/log/provisioning pointers are in the E0.

## Bounded interpretation and engineering conformance

Strongest support: real full-file delivery, successful pinned installation and
NumPy/Torch import, matching primary readback and both terminal witnesses, all
inside the complete bound. This replaces P15's header-only evidence for this
particular path with one observed complete success.

Strongest limitation: no native learning path was run. Earlier acquisition and
runtime failures remain evidence, including their partial files. The successful
local Windows direct route and earlier remote failures have different clients
and connection conditions; this is not a controlled proxy/TLS or interpreter
causal comparison. One import success does not establish runtime reliability or
retroactively lift a prior quarantine.

The original B04 RAW 12.0375 versus REQUEST_ONLY 12.375 and missing STRUCT pair
remain unchanged. Public-request conditioning remains a surviving scientific
alternative; the paired representation question is unanswered. Tuned same-host
headroom remains absent. This A result does not alter `DIRECTION.md` or Portfolio
science, lifecycle, priority, recast count, C consumption or UAV entry.

P17 executed the already accepted source. It adds no implementation machinery or
new section-4 scope beyond the P16 card's named task-specific process/node and
deadline control. The three CM comparison batches were already complete, and
this assignment was pure execution/collection. No section-5 source or runtime
budget breach is observed. Both actual admissions passed at their respective
nodes. The source-provisioning ref collision/stall was handled before acceptance
using the existing Git route while preserving the historical ref; that operation
did not acquire packages or create a second candidate invocation.

Mark `resources_unmeasured` for aggregate CPU, summed per-host process wall and
runtime peak memory. Full source-provisioning and engineering elapsed work also
remain unmeasured. The known candidate-command subtotal is 743.35 s historically
plus 174.5612299 s here, or 917.9112299 s; it excludes source provisioning and
control-plane work and is not total study elapsed or aggregate CPU. These optional
resource gaps do not annul the independently measured metadata-path result.
No timeout/lost-connection kill path was exercised by the successful invocation;
the P16 relative-clock-rate, ordinary scheduling and no-suspend assumptions remain.

## Prediction and owner boundary

The prelaunch DM prediction that the first local GET would acquire some Torch
body bytes is **supported** by the retained complete Torch body. Full-chain
readiness was explicitly uncertain; do not retrospectively claim it was predicted.
Owner prediction: **not taken (unattended)**. Current owner reviews returned []
at the allocation and intake boundaries, and relevant audit owner columns were
blank. No changed instruction or prediction was available to apply.

The [Chinese brief](../../portfolio/owner/briefs/capability_bound_semantic_currentness/2026-09-07_LOCAL-ACQUISITION-P17.md)
records this valid A result. Existing P2 card item `20260907-cbsc-006` receives the
actual P17 execution trace, without fabricating an owner reply or authorizing a
learner. Ordinary intake decisions remain here and in the audit ledger.

## Decisions this intake produces

1. **Object / technical:** (a) accept PATH_PREPARED at the one-invocation metadata
   ceiling; (b) retain header-only readiness despite complete primary evidence;
   (c) infer B04 repair or a runtime cause. Recommend/select **(a)**. The actual
   rule is satisfied; the absent learner observation limits the dependent claim.
2. **Object / next-task recommendation:** (a) return preparation of one fresh
   paired RAW/STRUCT B on the prepared runtime; (b) add an unchanged acquisition,
   import or historical-cause series; (c) silently rerun old B04/STRUCT under a
   changed interpreter. Recommend/select **(a)**. This preserves the existing
   scientific question while making the interpreter/comparison explicit.

Owner-delegated decision (unattended, 2026-09-03 instruction): (a) for each decision.
Both records are reversible. Owner flags: none; no close call, material critic
override or second recast. P17's one invocation allowance is finished; the A/B
objects have no consumption state. No new execution is allocated by this intake.

## Concrete next-task need and discriminator

Return through Root to Portfolio: commission a prospective card and exact command
binding for **one fresh paired training seed**, with both RAW and STRUCT in the
prepared CPython 3.12.3 prefix. Retain the accepted B04 sampled-opportunity credit,
observation/action/information semantics, CPU FP32/one-thread profile, final
update-48 native-return comparison, public-request rule context and MEI 0.25.
The original B04 card explicitly fixed the old interpreter; this is a prospective
new paired observation, not completion of that historical invocation under a
silently changed runtime. Preserve the old RAW as separate evidence, not the new
runtime's paired control. The fresh seed and exact source/output binding belong
in that next card; none is frozen or launched here.

The proposed work retains the B04 cost law: 2 arms x 1 new seed x 48 rollouts x
8 episodes, 2 x 48 x 4 x 4 Adam steps, and 2 x 2 checkpoints x 32 evaluations.
This is 768 training episodes, 1536 Adam steps, 128 evaluation executions and
136192 train/evaluation transitions; RAW's three fixed rules add 96 existing-tape
passes / 2304 action scores once. Propose the existing 600 s complete cap per arm,
1200 s summed caps, with pair publication inside STRUCT's cap. Actual work in the
new runtime is unknown; the old RAW 53.46 s is only a planning reference. There
is no nested search or additional diagnostic series. New exposure currently zero.

The accepted RAW/STRUCT comparator and baseline set are reused because their
observation, action, information and budget semantics match; changing the runtime
requires both new arms to share that declared condition. This recommendation
reuses the current B04 card/intake and changes no mechanism or comparator class.
No fresh literature claim or corpus search is needed for the technical access
finding. A complete cause diagnosis is not required before that bounded real B.

The next discriminator is the native paired return on that explicitly bound
runtime, retaining every outcome. P17 supplied the missing metadata path, not an
automatic learner allocation. Root can forward the observed complete cp312 input
and runtime facts to FRRIE under P17; separate allocations and failures remain
separate. No live invocation, pending collection or Pro request remains here.
