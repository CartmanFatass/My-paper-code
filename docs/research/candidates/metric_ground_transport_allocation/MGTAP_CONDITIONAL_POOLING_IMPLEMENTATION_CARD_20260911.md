Claim: the exact eligible COND encoder and separate COND/DENSE readout can satisfy the specified supplied-tensor technical contracts; this object measures no native performance.
Binding MARL structure: (d) other-agent non-stationarity or partial observability; the intended actor uses visible partner geometry to condition current user emphasis without observing partner intent.

# Conditional pooling implementation card — 2026-09-11

## 1. Authority and L0

Portfolio option A at response `ed0c4e1c3cd28be353253e8533bc89a261f25357`,
[MGTAP execution mapping](../../portfolio/pro_packets/20260911_five_chain_refill/EXECUTION_MAPPING.md#mgtap--exact-cond-implementation-and-one-encoder-only-fixture),
and Root's exact assignment allocate this implementation and **at most one complete
CPU FP32 encoder-only fixture, 60 seconds including imports, publication, creator
scratch cleanup and exit**. This is engineering acceptance, not a B or a frozen C.
The [Convergence intake](pro_packets/20260910_conditional_pooling_reentry/CONVERGENCE_INTAKE.md)
supplies scientific eligibility only. Future B work remains unallocated.

- Deliverable: exact COND operation, minimal separately named two-arm construction
  entry/readout, mirrored focused test, one technical acceptance or precise gap.
- Ownership: `C:/Projects/HMASD-worktrees/dm-n5-continue-20260904`, `codex/mgtap`;
  `experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/{geometry,conditional_pooling}.py`,
  the mirrored `test_conditional_pooling.py`,
  `scripts/run_mgtap_conditional_pooling_fixture.py`, and this direction's card/result/intake.
  Ordinary audit/owner records are appended through their existing routes. DM is the editing owner.
- Preserved semantics: source/design return [§§3–7](MGTAP_CONDITIONAL_POOLING_SOURCE_DESIGN_RETURN_20260910.md#3-one-actual-learned-operation-and-its-comparator),
  old REL/DENSE/H/two-master runner and command, shared UCOPE actor/critic/learner,
  native environment/reward, private initialization and RNG streams. No old command is relabelled.
- Acceptance: exact masks/query/normalization/empty/count/raw/parameter/gradient and
  primary/publication behavior within the bounded fixture; independent read-only high-risk
  review of the diff and reachable imports under Engineering Scope §7.3 before execution.
  Evidence-spec §11.8 limits the conclusion to tested properties. Full learner counts and
  common recurrent/critic copying are source review plus shape arithmetic, not executed coverage.
- Budget/stop: one fixture only, at most two standalone encoders, four forwards each on
  at most 16 rows of width108, one supplied-loss backward each, four synthetic paired
  readouts of32 scores per arm. Stop after its success or failure. A corrected source does
  not receive another fixture, full-policy smoke or replacement architecture.

Initial checkout was clean at `e672f8b37b1274174c5518d67705a9b08e51e51c`.
Reconciliation `56e98f583` incorporates assigned main `5bbae6d90`; the sole conflict
was the2026-09-10 audit. All33 distinct conflict-side rows survive, along with the
historical direction packet provenance. The merge was pushed immediately.

Engineering Scope §4 needs **none**. Source budgets remain2000 new attempt lines,
600 per runner; orchestration proportion is a review signal. No runtime framework,
registry, replay, telemetry or timing pilot is added.

## 2. Operation, interfaces and initialization

COND preserves `U20×3`, `V21×4`, `P64×41` and full `W64×108+b64`.
For raw user/UAV rows, masks are SINR component `>0`. Its query is the mean of the
first20 embedded components of visible UAVs, or zero. The visible-user softmax
uses `dot(eU,q)/sqrt20`. User context is the weighted sum times`nU/20`, or exactly
zero when no user is visible. UAV context is the masked sum divided by10, including
V's21st component. With no visible UAV, user weights are uniform. The preactivation
output is `(...,64)` from an input `(...,108)`; flattening never transfers entity state.

`make_encoder(kind, branch_seed, raw_state)` isolates the existing branch RNG domain,
preserves its exact initialization order and copies supplied common raw tensors.
NativeGeometryActor uses it, then the unchanged private GRU/head/log_std copies.
Both projections start at zero; DENSE retains its raw108→16 nonlinear branch and
zero hidden bias. The separate `build_cond_pair(seed)` is a **source entry only**:
it uses the existing common templates, domain`100000*seed+11`, separate branch
domain`100000*seed+12`, and independent critic copies. This fixture never calls it.
No native/training CLI or selected master is introduced for a future B.

The existing branch/encoder/complete-learner counts are2768/9744/69079 per arm.
The fixture measures the first two on its standalone encoders and checks the third
by arithmetic over reviewed source dimensions, without constructing an actor/critic.
Parameter matching does not imply equal function class, equal compute or equal learning.

## 3. Focused fixture and publication

Fixture label/seed8211 is a supplied-tensor test identity, not a selected training
master. Forward1 checks prescribed zero projections, common raw output, CPU FP32
parameters and private-construction RNG isolation. Forward2 uses explicitly
nonzero **fixture-only** projections and supplied sparse U/V maps; an independent
scalar formula checks all16 contexts. Rows cover empty sets, visible zero offset,
masked padding with nonzero offsets, opposite UAV queries, no-UAV uniform pooling,
one/two/twenty users, one/two/four UAVs, row permutation and all21 V outputs.
Forward3 changes an existing raw-only component and checks shaped output. Forward4
connects a supplied squared loss to every parameter block and input, with one
backward per arm. There is no optimizer and no claim that a policy learned or moved.
The FP32 comparison uses2e-6 absolute/relative tolerance for bounded input arithmetic,
not a repository-wide identity or scientific-equivalence requirement.

The separate `primary` reads exactly32 complete256-step final scores per COND/DENSE
arm, orders all differences and emits the mean and conditional evaluation SE.
The four synthetic panels cover above-MEI, the negative inclusive boundary, adverse,
and a damaged primary (duplicate/missing index, nonfinite score, incomplete episode).
Both boundary values are checked in the scalar reading rule. Damaged paired means/SE
are absent, while trustworthy DENSE rows remain. Each readout is published and read
from a closed JSON file; the complete fixture summary follows scratch cleanup.
No environment/trajectory produces those synthetic numbers.

The invocation is a short local focused check, within AGENTS §5's local short-check
route, using the declared existing Windows CPU interpreter. Current primary-control
compute/Monitor configuration was read. The portable future study remains remote-first;
this fixture creates no detached experiment or Monitor obligation. Before any encoder,
the entry runs the existing local `admit-memory` command; both available-memory values
must meet4GiB. The published exact command will give the outer child a60-second timeout
covering admission, imports, fixture, publication, cleanup and process exit. No retry.

Runtime output: `temp/directions/metric_ground_transport_allocation/exp/conditional_pooling_implementation_20260911_8211/`.
Creator scratch: this checkout's `temp/directions/metric_ground_transport_allocation/test/cond_pooling_20260911_8211/`;
the creator checks the resolved temp boundary and removes only that directory in`finally`.
The durable result/intake preserves the necessary summary, receipt, review and limits.
Root accepts later retention/reclamation; the shared authoring checkout remains in use.

## 4. Exposure, predictions and scientific limit

Allowed counts: standalone encoders2; forwards2×4×16 rows maximum; supplied backwards2;
synthetic readouts4×2×32 scores. Full actors/critics/checkpoint loads/environments/
trajectories/training/native or real evaluation/optimizer/profiling/search are all0.
All numerical validation fits within this one invocation. Source reading, authoring,
review and Git/publication support are separate incurred work, not zero-cost compute;
their complete wall/CPU is unmeasured. The fixture's process wall is measured once.
No full candidate throughput or activation-memory estimate is inferred.

DM prediction: the technical fixture passes; this says nothing about COND native
return. Owner prediction: `not taken (unattended)`. Success means tested technical
properties only. Failure leaves numerical acceptance incomplete, preserves actual
partial exposure and yields no scientific polarity or automatic second fixture.

The native tuned same-information headroom record remains absent. The potential
future comparison retains absolute MEI0.01 for the host-specific reason in source
return§6: an extra connected user's coverage contribution is0.014 before the SINR
term. This card does not freeze or fund that B. Its prospective readout is strict
above+.01, inclusive[−.01,+.01], below−.01, or incomplete. An above-MEI real result
would support one bounded package observation; inside would leave a useful benefit
unshown without equivalence; a loss would weaken this package; a damaged primary
would support no paired reading. None automatically authorizes continuation here.

Scientific-tools reading uses FOUNDATIONS §§2–4,6 and the empirical topic. The concrete
assumptions are that legal local rows and recurrence do not reveal partner intent,
the intact equally informed DENSE can respond to the same event, and one training
pair would not estimate training-population uncertainty. A tensor interaction and
gradient do not establish a useful learned action or return. Prior relevant literature
retrieval in source return§7 is reused; no changed mechanism or unresolved literature
claim requires a new search. Strongest support is the specific source-compatible
interaction. Strongest contradiction remains P75 REL−DENSE−0.02396310430506595, with
its inside-MEI second master; no synthetic score supersedes that native evidence.

## 5. Decisions this card produces

Object tier: options(a) implement and exercise exactly the allocated technical
contract,(b) change its architecture/check exposure,(c) proceed to real B.
Recommend and select(a). **Owner-delegated decision (unattended, 2026-09-03 instruction): (a)**,
executing the current Portfolio PRO_FINAL allowance. Owner flag:none. A new-card owner
item supplies asynchronous visibility, not another permission gate. Primary-control
unapplied owner reviews returned`[]` at preparation; relevant current audit owner cells
were empty. Technical acceptance/intake, including the actual review and fixture
receipt, follows in the existing result record. Stop there and return to Root.
