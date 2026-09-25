# Spatial demand generalization

## 2026-09-24 — Direct DM adoption and A2 prospective comparison

I actually take responsibility for the revisable question: how finite spatial-task training
coverage affects ordinary multi-agent control on held-out layouts and its specialization cost.
Direction `spatial_demand_generalization`, state `exploring`, lead runtime
`Codex DM (independent session)`. Actual task `01a0d6ab-ccf0-76d3-8aa3-4489b9d2ee10`,
host `local`, authoring checkout `/home/fires/.codex/worktrees/c2a5/hmasd-wsl`,
branch `codex/spatial-demand-generalization-a2`. The clean independent checkout was based
on fetched published main `2802f26d6c42b107c4738477dc697f0a0c6c8a9a`. No accepted operation
from another task is adopted. B19 and S7 B09 remain with their existing leads and observers.
This is the third authorized research track. No App messages are sent.

### Scientific basis and reuse of complete Pro advice

Read the current constitution, direct-DM developer instructions, scientific-tools and
research-engineering methods, current RESEARCH background/plan, and the **complete Answer
and Decision** in the [adopted programme at 2802f26d6](https://github.com/CartmanFatass/My-paper-code/blob/2802f26d6c42b107c4738477dc697f0a0c6c8a9a/docs/research/archive/2026-09-24/RESEARCH-question-led-programme-adopted.md#answer).
The pinned archive preserves the original complete question, answer, source identities and
decision; its question key is
`hmasd:05feea016abd4f720d37e50860f91770639d4cab46466d8ecbc71d48a3ea127d`.
I adopt A2 without a changed premise or key comparator, including its adverse-result branches.
This reuses that complete advice under constitution section 5; ordinary implementation and
prospective exact-world binding do not call for another Send. No new Pro operation exists.

The [published shared background](https://github.com/CartmanFatass/My-paper-code/blob/2802f26d6c42b107c4738477dc697f0a0c6c8a9a/docs/research/RESEARCH.md)
changes this design concretely. B16/B17 make LOCAL1 the competent ordinary working comparator,
instead of inferring skill value from the weaker SET baseline. Keep B17's limited H6 N4 use,
B15's inconclusive joint confirmation, and B18's missing M endpoint. B18's F own-learning
does not supply our U endpoint. The repeated auxiliary/encoding/entropy reversals argue for
a direct training-coverage comparison rather than adding a representation mechanism or a
proxy success condition. B19 changes roster coverage; A2 changes layout coverage at fixed N.
They may share software but are neither replications nor interchangeable estimates.

For the specific literature bridge, read real source extraction
`/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/fulltext/MARL-0457.jsonl` (CEC), especially
units `u00034` (p2), `u00059–u00060` (p3), `u00141`, `u00148` (p6), and `u00174` (p7).
The original distinguishes task and partner diversity and observes a generalization versus
specialization tradeoff after single-layout fine-tuning. This supports reading both held-out
use and seen-layout cost. It does not establish UAV transfer, independent-partner coordination,
or the value of this 50/50 mixture. No synthetic My-lib fixture, reading-model judgment,
whole-library review or paper throughput is used as empirical evidence here.

### Fixed scientific object, worlds and cost (before result execution)

Object `s1_spatial_coverage_a2`, planned tag `s1_spatial_coverage_a2_s260925101`.
Two fresh ordinary LOCAL1 fits, ordered U then M, each 45 complete rollouts of 16 lanes
and H500 at N6/c10, Scenario1, 50 static users, free-space channel. Same original native
objective, observations, actor/critic rights, action clipping, learning rates, low-level
entropy .05, k10 recurrent/chunk clock, masks, normalization, update semantics and endpoint.
LOCAL1 has one trainable FiLM category, no trained high-level or discriminator, no central
actor snapshot; the existing central critic retains its existing legal state. No new family
label, global layout input to the actor, communication, privileged mask or observation field.

Use B16's actual configuration: hidden size 256, 8 heads, 2 layers, 15 PPO epochs,
sequence batch size 32, CPU float32 and torch threads 4. Observation/state normalization
remain disabled; the actual value-normalizer and optimizer initial states must match.
No old trained weight, normalizer or optimizer is loaded. Both fits use model/learner seed
`260925101`, and independently reproduce and compare the actual initial tensor, normalizer,
optimizer, sampler, runtime and post-construction RNG state before sharing initial evaluation.
Config-only constructors use seed `260999999`, with no scored environment transitions.

Training world addresses: for zero-based rollout r=0..44 and lane l=0..15,
`world_seed = 261000000 + 1000*r + l`. U uses uniform on every lane. M uses uniform iff
`(l + r) % 16 < 8`, otherwise cluster. Thus M has exactly 8 uniform and 8 cluster lanes
each rollout; each physical lane changes family under a fixed rotation (22 or 23 exposures
to each family over 45 rounds). Every round gets fresh world seeds, including for the same
family. The 720 (r,l) addresses per arm are fixed now; U and M use the same address at a
given (r,l), but different generators need not yield the same physical world. Common-family
initial geometry is compared where the generators coincide. The first M rollout is lanes
0–7 uniform and 8–15 cluster. No schedule search, resampling of unfavorable worlds, or
outcome-based lane changes.

World creation/reset uses each native environment's seeded local generator inside a
preserved learner-RNG context; verify that Python/NumPy/Torch learner state is unchanged.
Policy/update RNG behavior otherwise follows the fixed ordinary source, including the
private RolloutBuffer shuffle generator. Record actual seed mapping and RNG digests;
seed names alone do not prove common physical initialization. Persist every complete reset
scene, with family/lane, states, observations and positions, before its first transition.
Do not reset completed environments merely to create an unused next world.

The only evaluation stages are one common true initialization and U-final45/M-final45.
For each stage evaluate uniform, cluster, hotspot in that order, each at these 32 fresh
world seeds with deterministic mean actions and the same execution clipping:

| Family | Inclusive world seed range | Training relation |
| --- | --- | --- |
| uniform | 262000000–262000031 | both arms saw this generator, with different exposure |
| cluster | 262010000–262010031 | only M saw this generator |
| hotspot | 262020000–262020031 | fully held out from both training arms |

Within a family, all three policies must have byte-identical actual initial states,
observations, user positions and UAV positions. Evaluation uses private target agents,
strict weight/normalizer sync, frozen normalization, no training storage or updates;
verify learner/optimizer/sampler/global RNG isolation. Sharing the initial panels is
allowed only after full actual initialization equality. No training or evaluation world
above is an already selected development world of B16/B19. Tests use separate tiny seeds
and horizons; no production evaluation world is executed to choose implementation or method.

Dominant planned work: each arm 360,000 team transitions / 2,160,000 UAV action rows;
2 fits total 720,000 training team steps. Fixed evaluation is 3 policies × 3 families ×
32 worlds × 500 = 144,000 team steps / 864,000 action rows, 288 episodes, zero updates.
Total 864,000 team steps / 5,184,000 UAV action rows. Each complete fit has 45 outer updates,
50 recurrent chunks per lane/UAV, 150 minibatches × 15 epochs per update, hence 101,250
actor and 101,250 critic optimizer calls if the inherited real sampler contract holds.
Both arms together have 90 outer updates and 202,500 calls of each optimizer. No dropped
time tail or short sequence batch is expected. Count actual sampler yields and updates.
Support work includes implementation, tests, review, cold imports, storage and full reading;
wall time is unknown rather than borrowed from B19. Node, interpreter, supervisor and floor
come from the current compute table; prefer wsl_4070 and record actual suitability before
choosing. Actual launch admission is separate from this plan and uses fresh node resources.

### Prediction and reading

Primary directional prediction: on hotspot, mean `J(M45)−J(U45)>0` **and** mean
served users per step `S(M45)−S(U45)>0`. J is the native per-step team objective,
restored from scalar reward by N6, and checked against `.7*coverage + .3*quality −
energy_penalty`. In S1 this last field is the height term, not battery energy or safety risk.
Read uniform costs alongside the primary result; read cluster as seen-generator use.
For each family report each endpoint minus the true common initialization, per-world
differences and losses, absolute J/service, eligibility, unserved capacity, quality and
height components. Keep all worlds and both positive and adverse trajectory consequences.

Strong alternative: ordinary local feedback already provides the useful hotspot behavior,
while replacing uniform experience changes finite optimization or a particular spatial
preference without worthwhile held-out gain. This is a complete training-mixture comparison,
not identification of a learned spatial mechanism. Cluster-only improvement supports
seen-family specialization; opposite J/service signs are a native tradeoff; small hotspot
gain with substantial uniform loss need not justify replacing U. No fixed proxy prediction
is required. A negative pair does not disprove all task-distribution learning.

Hotspot uses the existing fixed area center, 70% of users with uniform radius in area/3
and uniform angle (not uniform disk area), remainder uniform. Cluster uses five random
centers, Gaussian perturbations and boundary clipping. Generator holdout does not prove
disjoint state support, arbitrary hotspot locations, moving demand or new-partner coordination.
Each arm is one training instance; 32 nested worlds describe these fixed policies and do
not increase training n or provide training-population confidence. No MEI/confirmation verdict.

Stop at final45 and the nine fixed panels. No mixture ratio search, earlier endpoint
selection, moved hotspot, extra seed or extension to rescue this batch. Technical failure
preserves started fits, progress, native exit and every surviving output; a missing endpoint
is an incomplete comparison, never filled from B19 or another run. No automatic retry or
`--resume-jobs`; uncertain acceptance is reconciled against the same native handle.
After reading, compare useful recurrence, a materially revised question, unowned independent
work or an evidence-supported stop using current project evidence and actual cost. Positive
exploration does not automatically launch confirmation; section 5 advice must cover any
new consequential decision and actual confirmation claim/plan.

### L0 — bounded A2 implementation and acceptance

Deliver a disposable A2 layout adapter, paired runner and compact analysis under
`experiments/candidates/spatial_demand_generalization/a2/`, entry
`scripts/run_spatial_demand_generalization_a2.py`, focused tests under matching
`tests/experiments/candidates/spatial_demand_generalization/a2/`. Selectively materialize
only necessary published source/dependencies from B19 source
`bfb4fd356a01024ef04c967c4768263f114e5a17`; enumerate them and retain their byte identity.
Do not copy its dirty checkout, merge its experiment history, run B19, alter historical
output contracts or change shared learners/environments. If a core difference is required,
surface it explicitly before acceptance and obtain the corresponding independent review.

The Implementer may own these code/test/entry paths and the explicitly enumerated fixed
dependency materialization, not this notebook or RESEARCH, and must not stage/commit while
the DM edits records. It returns diff, checks, deviations and risks; no science choice,
result launch, Pro, App messaging or child delegation. DM accepts the result. Preserve
world/learner RNG separation, real LOCAL1 initial state and buffer masks/bootstrap/update
path, terminal reset behavior, legal input rights, and evaluation isolation.

Checks must exercise actual native uniform/cluster/hotspot construction on tiny independent
worlds, all 45 lane schedules, shared model/normalizer initialization, common-family
physical identity, real small collect/storage/sampler/update, exact production count
arithmetic and evaluation no-update/isolation; independently recompute J/service from
native traces. Fault injection must leave completed reset evidence before any step and
incomplete summaries rather than fabricate endpoints. No new framework or alternate
scientific retry mode. A high-risk RNG/evaluator/runner change receives independent Reviewer
coverage before acceptance. Source publication precedes actual launch.

Runner outputs go to `runs/spatial_demand_generalization/<tag>/`: compact config, summary,
native admission/manifest/status, per-world panels and paired readings in Git; bulk
checkpoints, training streams, reset scenes and traces under `raw/` on durable configured
storage, with bytes and SHA256 in existing artifact metadata. Keep learner movement,
actual training/evaluation/optimizer counts and measured resource scope. Publish this
direction's registration/routing to main before launch, then publish material read results
and useful affected shared understanding independently. Accepted work is observed by this
task's `tools/hmasd_wait.py`; checkpoints rearm the same handle without restarting it.

## 2026-09-24 — Prospective implementation checks and node choice

The complete 45-round schedule check corrects a descriptive arithmetic error above, before
any production exposure. Under the unchanged rule `(lane+r)%16<8`, M's per-lane uniform
counts are `[24,23,22,21,21,21,21,21,21,22,23,24,24,24,24,24]`, with cluster counts 45 minus
these values. Thus the per-lane range is **21–24**, not the previously written 22/23.
Every rollout remains exactly 8/8, each family has 360 training lane-episodes, and all seed
addresses, fits and team-step costs remain unchanged. The executable rule takes precedence
over that mistaken explanation; no outcome-based schedule alteration occurs.

Source mapping and DM byte check found 17 required candidate dependency files (320,351 bytes)
materialized exactly from `bfb4fd356a01024ef04c967c4768263f114e5a17`; the LOCAL1 builder,
native adapter, action/RNG helpers and B11/B15 trace/isolation helpers retain their frozen
bytes. B13/B02 are necessary transitive imports, not active scientific comparisons. Shared
learner/config/environment core in this closure already matches main; no core repair is
included. A2 uses its own disposable factory and runner instead of mutating frozen modules.

Select **wsl_4070 CPU**, the configured remote node, preserving LOCAL1's CPU/float32 path
and four torch threads. The first read-only suitability snapshot showed 20 logical CPUs,
13,920,055,296 bytes MemAvailable and the already-running S7 B09 GPU process at about
2 GB RSS; this snapshot is not launch admission. Interpreter is the configured
`/home/wu/.venvs/hmasd/bin/python` (Python3.10.21, NumPy1.26.3, Torch2.7.0+cu118), supervisor
`/usr/local/bin/agent-task`. Recheck actual physical/effective memory at release. No old
SIGSEGV is claimed repaired, and neither existing research process is altered.

Registration and exact prospective notebook are published on main/direction at
`943e3e9a72852017840d1fdb0ef595a9e44f8a3d`, preserving the concurrent Root start update.
Remote network Git operations require the configured `zsh -lic` environment; two initial
source-transfer helpers without that context were stopped after their identities were
checked, without touching research processes. Configured-context fetch succeeded. Its
background automatic repack reported an existing bad-tree warning; no repository cleanup
or unrelated repair is attempted. The actual A2 source snapshot and required artifacts
will be verified separately before execution.

## 2026-09-24 — A2 implementation accepted for actual-node verification

DM read the implementation and accepts the fixed comparison after the independent Reviewer
closed both concrete findings. Exception-time evaluation now retains available raw arrays,
observed/fully-recorded transition masks, component sums and content hashes; a failed
unstarted panel reports that trace allocation never happened. Hard process termination
cannot execute this exception handler and remains an incomplete technical event. An A2-owned
checkpoint writer keeps the inherited weight/normalizer payload but correctly identifies
the direction, object, tag, U/M arm, rollout and launch SHA. It adds no training-resume claim.
The fixed dependency bytes and successful-run scientific exposure remain unchanged.

On the configured local CPU interpreter, the final focused A2 suite passed **7 tests in
9.00 seconds**. The small native test uses 16 training lanes, two H20 rounds, separate
technical worlds and reduced model/update sizes; it exercises uniform/cluster storage and
updates, actual common initialization, world/reset identity, private sampling, evaluation
isolation, checkpoint loading and independently reconstructed native J/service. Fault tests
cover before/after the first training step, evaluation failure after two actual transitions
(two observed, one fully recorded), and failure before trace allocation. The unchanged
`tests/hmasd/test_discoverer_entry_masks.py` also passed both parametrized cases in
1.63 seconds, covering previous-done masks through the real discoverer update path.
These are technical checks, not exposure to the declared production evaluation worlds.

Final reviewed A2 runner SHA256 is
`3d0e07348075e6cd46b2a85525a166af2901f41089b2b9a83237e5424afb19cb`;
test SHA256 is `ed6760a92a85e43e074290524634a1b06f8bbd179fc1fca71c1ff1302a345921`.
Reviewer traced layout generation, initialization/RNG, fixed-N reset, raw actions/logprobs,
storage/entry masks/bootstrap/private sampler, evaluator and admission, then read the two
repairs; no material finding remains. Cold imports, compilation and whitespace checks passed.
Run the same focused suite once on the configured actual node to check its distinct runtime,
then release this accepted, published implementation through the native launcher after its
fresh resource/pause/lead checks. No result-bearing A2 attempt has yet been accepted.

The pre-release refresh reached main `ee734907ecc936b27a99d83597d613efaf8bb9bf`.
Its [B19 background update](https://github.com/CartmanFatass/My-paper-code/blob/ee734907ecc936b27a99d83597d613efaf8bb9bf/docs/research/RESEARCH.md)
reports a complete, bounded positive ordered-roster comparison and a competent fixed-N6 arm;
it does not answer spatial-family coverage. This supports retaining our ordinary LOCAL1
reference without changing the A2 comparator, prediction, fixed worlds or cost. B19 is now
complete rather than still executing as at registration; A2 pause/lead/routing are unchanged.

## 2026-09-24 — A2 accepted and native observation armed

The actual configured `wsl_4070` interpreter passed the same **7 focused tests in 7.13 seconds**.
Its dedicated authoring checkout is `/home/wu/hmasd-worktrees/spatial-a2-01a0d6ab`.
Source staging completed despite the shared clone's pre-existing automatic-Git-maintenance
and missing commit-graph-object warnings; no shared Git repair or history rewrite was made.
The accepted source is published `d22b608e8d063ceac5c944426bd35a2289c5ebf6`, including the
reviewed runner/test bytes above. This is the first A2 result-bearing launch request.

Configured supervisor task `a2_s260925101_d22b608e` entered the configured network/run shells
and invoked `scripts/hmasd_launch.py launch --node wsl_4070 --snapshot`, bound to the fixed
direction, lead, SHA, output tag and entry seed. **Native admission accepted at
2026-09-25T04:17:16.295481Z** (2026-09-24 PDT), independently of the outer task-start signal.
Actual-node preflight measured 13,010,100,224 physical/effective available bytes against
4,294,967,296 required; current published control was main
`ee734907ecc936b27a99d83597d613efaf8bb9bf`.

Operation reference:
`/home/wu/projects/HMASD/.git/hmasd-admission/2f5e96dfbf13660f91219817c5a01198a6725b919d74e9e85425d86c37272446.json`.
The retained source snapshot is
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/2fc6a6f7e27347e983ce2e7589756d8c`.
Native supervisor/runner PIDs are 609757/609758, with start identities in the
[manifest](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101/launch-manifest.json).
Complete outputs remain under
`/home/wu/hmasd-worktrees/spatial-a2-01a0d6ab/runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101`;
stdout, stderr, eventual process-exit and raw evidence use the normal runner layout.
The launch manifest, admission preflight, launch status and U/config were copied to this
direction's local run folder and byte-hash matched to the native files. Configs are per-arm;
there is no batch-root config file. Bulk evidence remains on the actual node for terminal
collection and verified recovery; nothing is deleted.

`tools/hmasd_wait.py` is armed for this task, generation 1, at
`/home/fires/.local/state/hmasd-wait/01a0d6ab-ccf0-76d3-8aa3-4489b9d2ee10`.
Its private request is
`temp/directions/spatial_demand_generalization/a2-native-wait/request.json` and names the
same operation through native status, with a 30-second read-only probe and 1500-second
window. The first drain observed accepted/running with consistent records and zero probe
errors at 2026-09-25T04:18:17.644765Z. No result has been interpreted. Yield to this
observer; a checkpoint rearms this same handle, and terminal evidence is reconciled and
read without an automatic runner retry. This unchanged batch start needs no main/index edit.

### First observation checkpoint — 2026-09-25 04:42 UTC

Drained generation 1 / wake `6bebbac8-26e6-46ad-8529-1ec4928c0c4f`, checkpoint event
`ebe3f0c9d7397378618fb27c`. The same native operation remains accepted/running, its process
identities and records agree, and observation has zero errors. Current U arm summary reports
one started fit, 208,000/360,000 training team steps collected/stored and 25 completed updates;
its 48,000-step common-initial evaluation completed with zero evaluation storage/optimizer
calls. M is unstarted. The batch summary's initial arm fields are not a live fit counter;
the more recent arm summary supplies this progress. No endpoint is read. Current node control
still records the lifted pause, and no newer owner stop/pause has arrived. Consume this
checkpoint and rearm the same operation; retain routine progress here until the result boundary.

At the second checkpoint (2026-09-25 05:08 UTC), generation 2 / wake
`66a4d160-90df-4d4c-bb25-04955b414f0f` / event `71732bee4ad65d0a6c81e531`, the same
operation remains accepted/running with consistent identities and zero observation errors.
U reports complete: 360,000 training steps, 45 updates, and 96,000 common-initial/final
evaluation steps with zero evaluation storage/optimizer calls. M has started its fit and
reports 56,000/360,000 training steps collected/stored and six completed updates. Thus
two fits have actually started; the batch-level aggregate still reflects the completed U
arm while M is live. No paired scientific result is read or investment changed. Current
node pause remains lifted. Consume the checkpoint and continue observing the same handle.

At the third checkpoint (2026-09-25 05:34 UTC), generation 3 / wake
`75887af3-e353-4585-b778-49ac4a3ae5ab` / event `2ac9e4e65b0f34e262b0977d`, native
execution remains accepted/running and consistent with zero observation errors. M reports
264,000/360,000 training steps collected/stored and 33 completed updates, without a reported
failure; its final evaluation has not started. U remains complete. No newer pause is recorded
or owner stop received. Consume this checkpoint and rearm the same operation for its remaining
training/evaluation and terminal evidence; no endpoint interpretation or new launch occurs.

## 2026-09-24 — A2 complete: modest held-out gain and heterogeneous local costs

The fixed A2 batch completed and DM acceptance is complete. The native witness reports
ordinary exit 0 at 2026-09-25T05:46:27.102003Z, with the original accepted supervisor/runner
identities. Generation 4 wake `c96fc795-ff8f-4f92-9f8c-667b60db7ac6` and READY event
`ef057baf6478cdd5605e6938` were read in full and consumed after collection/reading; no launch
observation remains active. Neither exit zero nor the observer was used as scientific acceptance.

### Complete evidence, actual cost and retention

Both arms finished 45 updates and 360,000 training team steps, with 101,250 actor and 101,250
critic optimizer calls per arm. U received 720 uniform lane-episodes; M received 360 uniform
and 360 cluster. Actual totals are **2 started/completed fits, 720,000 training + 144,000
evaluation team steps, 5,184,000 UAV action rows**, nine panels and 288 evaluation episodes.
Evaluation stored nothing and executed zero optimizer calls. U/M scientific arm wall times
were 43.9839/42.7403 minutes; paired scientific wall was 86.7289 minutes, and native admission
to exit was 89.1801 minutes, including startup outside the timed scientific body. Process CPU
user/system were 20,474.0635/48.9532 seconds; process peak RSS was 1,830,112 KiB (1.7453 GiB).
This scope excludes other processes and peak scratch usage. Implementation, review, retrieval,
verification and reading are additional work, not hidden extra fits.

Independent post-run reconstruction covered all 144,000 evaluation transitions: service and
eligibility from link matrices, c10/unique-user/eligibility constraints, quality and height
components, native J versus six times learner scalar reward, action clipping and transition
continuity. Every per-world metric/difference and adverse-world list matches the summaries;
maximum panel-J roundoff was 1.28e-15. Actual initial scenes agree across the three policies
within each family. All 90 training reset scenes match the fixed seeds/family schedule and
shared uniform lanes; all four checkpoints load with the right identity and identical U/M
initial tensors/normalizers. All 45 sampler/update rows per arm and 44 reset boundaries pass,
evaluation preserves learner/optimizer/RNG/runtime state, and all 21 recorded source digests
match the accepted published commit. Both logs are empty; no failure or replacement endpoint.

The **136 original native files / 1,088,005,899 bytes** were copied and checked individually
against the actual node, then independently copied and rechecked at
`/home/fires/hmasd-artifacts/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101`.
The native output directory recorded above and this task's local run directory also remain.
Canonical inventory SHA256 is `e7d60fe78da56f81a437b29da3f165005f9f1e20d96c9d0013db3544f840ffcd`:
UTF-8 JSON array ordered by relative path, objects with path/bytes/sha256, sorted object keys,
comma/colon separators and no final newline. The original batch summary SHA256 is
`c766f6642fad258357f4fd555a122569ad5e13e2484e9a603b009b39cc82a71b`.
Compact original JSON is published without alteration; raw traces/checkpoints/streams remain
outside Git with their runner hashes. The derived world-difference figure is separate from
this original-file inventory.

Source-snapshot GC first refused to inspect protected own process 660. Its documented
read-only sudo process scan then found the original snapshot eligible; preview and apply
removed only `2fc6a6f7e27347e983ce2e7589756d8c` after the verified retention above. Claims,
manifest, exit witness, outputs and authoring checkout remain, and source d22b608e8 stays
durably reachable. No other operation or worktree was removed.

### Fixed endpoint and every adverse family

Values below are **native J / served users per step**, averaged over each family's 32 worlds.
These are one trained U and one trained M; world count does not increase training n.

| Family | Common initial | U45 | M45 | M45 minus U45 |
| --- | --- | --- | --- | --- |
| hotspot, primary held-out generator | .111314273 / 12.160938 | .361673636 / 23.241375 | .380242622 / 24.182125 | **+.018568986 / +.940750** |
| uniform, original training family | .154089815 / 14.979688 | .479379473 / 31.712687 | .488402765 / 31.712625 | +.009023292 / -.0000625 |
| cluster, seen by M | .134416911 / 13.669563 | .457801889 / 30.079625 | .497966756 / 32.167438 | +.040164866 / +2.087813 |

The prewritten **two hotspot mean directions are met**. This is an exploratory directional
observation, not confirmation or equivalence. On hotspot, J improves in 22/32 worlds and
service in 20/32; 12 worlds lose at least one. On uniform the corresponding counts are 19/32,
15/32 and 17 adverse worlds; near-zero mean service difference is not proof of no cost.
Cluster has 24/32 J gains, 22/32 service gains and ten adverse worlds. The worst paired
J/service losses are hotspot seed 262020012 (-.074145446 / -5.690), uniform 262000008
(-.067627130 / -5.442), and cluster 262010028 (-.069422559 / -5.266).
All 96 paired differences and every adverse seed/value remain in the
[original summary](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101/summary.json);
the [derived figure](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101/a2_world_differences.svg)
shows their spread without a training-population interval.

U/M own-learning J and service gains are respectively hotspot
(.250359362, 11.080438)/(.268928349, 12.021188), uniform
(.325289658, 16.733000)/(.334312950, 16.732938), and cluster
(.323384978, 16.410063)/(.363549844, 18.497875). Both policies improve J in every world;
hotspot service still falls below initialization for U at 262020011 (-3.466) and for M at
262020015 (-.460). All uniform/cluster own-learning J/service differences are positive.
Ordinary uniform training is a competent source of substantial held-out use.

Hotspot M-minus-U changes are coverage +.018815, quality +.017815886, height penalty
-.000053721, eligible users +2.264125 and eligible-but-unserved users **+1.323375**. More
eligibility did not all become service. Uniform's J increase accompanies higher quality
and lower height penalty, with essentially unchanged mean service and fewer eligible users.
Cluster has service +2.087813, eligibility +1.796000 and eligible-unserved -.291813.
Height is the S1 penalty term, not measured battery energy or safety risk.

### Explanation update and next decision

This pair strengthens the limited proposition that the fixed ordinary mixture can add use on
the held-out hotspot generator beyond a strong U endpoint. The observed gain is not confined
to seen cluster, and a substantial *mean* uniform service loss did not appear. It does not
identify pure task-support coverage, a learned spatial representation, or a training-population
effect. Sampling/optimization variation between complete training programs and a specific
fixed-center preference remain live alternatives. The small mean gain and many adverse worlds
also make blanket replacement unwarranted. Generator holdout is not disjoint physical support,
arbitrary hotspot locations, moving demand or new-partner coordination.

Current main `c543bc7efe5af9e497c67859f47e9ea0ba50202c` preserves B19's bounded roster result
and its own fixed B20 confirmation; neither is an independent replication of A2. The original
adopted Pro advice covers reading this fixed batch, but explicitly requires a concrete next
choice between reproducibility and changed task family. It does not cover a new actual
confirmation claim and seeds. I will now obtain that focused criticism, comparing a fixed
fresh-training replication proposal with a cheaper frozen-policy spatial-dependence observation
and stopping if neither changes a worthwhile judgment. No extra fit, alternative endpoint,
mixture search or moved-hotspot evaluation has been accepted; the existing A2 batch is closed.

The complete result is published at `3453c67f1c9eb748300a4dca9746bf88e52119b9` on this
direction branch. Its owned RESEARCH standing, directly affected training-coverage background,
A2 plan and routing were independently published to main at
`4fde2d73466fc80d91c3afbbbf0e3afc9f3ba8a1`, preserving the other DMs' B20/B09 entries.

## Pro question 2026-09-24 a2-replication-or-spatial-dependence

Conversation: new. Subject: `spatial_demand_generalization`.

Question: Given the complete modest A2 gain and its adverse evidence, should the next useful
investment be the concrete five-pair conditional-mean confirmation below, the cheaper
frozen-policy location-dependence observation below, a justified smaller/materially different
comparison, or stopping current investment? Criticize the **actual claim and fixed five-pair
plan**, including whether its inferential and practical value warrants roughly 7.43 hours.
If the frozen-policy observation cannot change that investment decision, say so rather than
selecting it just because it costs no fit. This is a direction decision, not a project review
or a request for more architectures. Return MATERIAL_DISSENT yes/no and the decisive reason.

Standing: A2 is fully read and accepted, 2/2 fits and nine panels. Hotspot M-minus-U is
J +.0185689864 / served users +.940750; 12/32 worlds are adverse in either quantity, including
a worst -5.690 users. Uniform is +.009023292 / -.0000625 with 17 adverse worlds, not an
equivalence result. Cluster is +.0401648661 / +2.0878125 with ten adverse worlds. U itself
gains +.250359362 J / +11.080438 users on hotspot relative to true initialization. M adds
eligibility +2.264125 but also eligible-unserved +1.323375. Complete per-world arrays,
components, both own-learning readings, hashes and native-count checks are in the preceding
result entry and original summaries. One training instance per arm leaves optimization/seed
variation unresolved; fixed-center spatial dependence is another live explanation, not a
diagnosed mechanism. The previous adopted Pro answer covered this comparison and its reading,
but not the new actual claim, seeds or uncertainty rule below.

Preferred proposal to challenge: **C01, five new paired blocks / ten fits**. Read
`CLAIM_layout_coverage_conditional_mean_20260924.md` at source_sha in this direction directory.
It specifies fresh model seeds 263000101..105; independent per-block training worlds starting
264000000+100000*b, plus 1000*r+lane; shared new evaluation worlds beginning 265000000,
265010000 and 265020000. The actual A2 U/M program, 360k per arm, common initialization,
final45, lawful LOCAL1 inputs, raw-action PPO and frozen evaluation remain unchanged.
The five block-mean hotspot J and service differences are the units. Both marginal two-sided
95% Student-t lower bounds (df4) must be above zero under the fixed joint sign rule; otherwise
the joint claim is not established. Uniform costs, cluster, own learning and every loss remain
parallel secondary readings. There is no noninferiority, next-run reliability or arbitrary-
hotspot claim; no pooling A2 or treating worlds as training n. About one added served user
at equal training/inference is a practical reference scale, not a fabricated minimum margin.
Five seeds do not establish the t model or sufficient power. No additional block or rescue.
My current reason to favor replication is that neither more worlds nor another demand center
can tell whether the positive training-program contrast survives fresh training. Challenge
whether this narrow conditional program-mean answer is important enough at the observed scale.

Concrete cheaper alternative: a **new, separately prospective 0-fit observation** of the
two retained A2 final policies. Use 32 fresh base worlds (267000000..267000031) and four
predeclared hotspot centers at (.35,.35), (.35,.65), (.65,.35), (.65,.65) times area size.
Keep the same 35 radial/angle draws, radius area/3, remaining 15 uniform users and initial
UAV positions within each base world; shift only the dense group's center and recompute the
actual initial observation/state/physical metrics before evaluation. These centers keep the
radial disk inside bounds, avoiding an added clipping rule. Two policies ×4 centers×32×500
=128,000 team steps /256 episodes, no training and no initial-policy evaluation. Read each
center's paired J/service mean, the equal-weight center average and all adverse worlds;
do not pool this with A2 or call centers training replicates. A gain reversal would show
location dependence of this fixed pair, not identify a learned center mechanism or refute
the original fixed-center result. Consistent gains would still not establish training
reproducibility or arbitrary-center robustness. No such worlds have been executed. This
would need a small disposable layout/evaluator change, native-scene checks and review.
Does this discriminate the investment decision, or is it a peripheral
observation? Do not treat it as a route to rescue or broaden the original A2 claim by default.

Prospective cost: C01 is 3.6M training +720k evaluation =4.32M team steps /25.92M UAV action
rows, ten fits, 450 updates and 1,012,500 calls of each optimizer. A2 measured 89.18 minutes
admission-to-exit per pair, so five sequential pairs suggest 7.43h before new contention/support;
around 5.44GB native artifacts plus verified copies. The alternative is 0 fit/128k evaluation
steps, 256 episodes; actual new wall is unknown and its implementation/scene validation,
review, staging, collection and reading are not free. No next run is accepted. A complete
positive A2 does not entitle either proposal to compute; stopping is a valid reasoned choice.

Context (paths marked source_sha resolve at the full question commit supplied in the message):

- Governance: `docs/project/OPERATING_CONSTITUTION.md` sections 1–5, 7–9 at source_sha.
  Owner delegated this direct DM's scientific continuity and ordinary decisions; pause is
  lifted, three result-track runtime ceiling remains, and no newer owner stop has arrived.
  Pro advises; the DM chooses and independently publishes. No App cross-task messages.
- Methods: `.agents/skills/hmasd-scientific-tools/SKILL.md`, Update the working explanation,
  Confirm a claim, Comparators and MARL information, Statistics, Cost and exposure, Pro, at
  source_sha. Use engineering Checks and review / Execution and admission only if a disputed execution/cost
  premise needs them; no extra ceremony or new record types.
- Current shared understanding: `docs/research/RESEARCH.md` at
  `4fde2d73466fc80d91c3afbbbf0e3afc9f3ba8a1`, the A2 training-coverage paragraph, A2 standing
  and A2 plan. B19/B20 concern roster coverage and are not A2 replications or evidence that
  this five-pair plan will succeed. Their existing work is not this task's responsibility.
- Frozen A2: the initial prospective entry in this NOTES and accepted implementation
  `d22b608e8d063ceac5c944426bd35a2289c5ebf6`. Complete result entry, original batch/arm
  summaries and nine panel JSON files under
  `runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101/` are published at
  `3453c67f1c9eb748300a4dca9746bf88e52119b9` and also present at source_sha. Read the means,
  adverse arrays and cost, not just the boolean directional verdict. Native NPZ/checkpoints
  are retained outside Git at the recorded paths; I verified them, but do not claim you read
  them if the connector cannot access them.
- Prior advice: `docs/research/archive/2026-09-24/RESEARCH-question-led-programme-adopted.md`
  at source_sha, Answer section four (A2) and section eleven (results that change priorities).
  It recommended a concrete choice between repetition and changed task family after a
  useful A2, rather than automatic encoder changes. Other archived rules are not governance.
- Actual proposed confirmation: the draft CLAIM named above at source_sha. Address its
  estimand, pairing, shared-world conditioning, power/interval assumptions, practical scale,
  selection exposure, costs and fixed failure/stopping rule. No fresh data have been exposed.

Constraints: no training or evaluation, no experiment implementation, no edits outside the
empty `### Answer` under this unique question heading. On branch
`codex/spatial-demand-generalization-a2`, fetch the latest target NOTES blob before writing
and use its actual blob SHA. Preserve the question and every other byte; stop on overlapping
edits. Report the actual commit on success; if writing fails, return the complete answer in
chat rather than a SHA, receipt or link. No chat-memory substitution for pinned sources.

Return: distinguish observations, strengthened/weakened judgments and still-live explanations;
choose the smallest useful next investment with its discriminating prediction and actual scope.
For the C01 draft, give MATERIAL_DISSENT yes/no, strongest material objection and any concrete
necessary revision of the actual claim/plan. A hypothesis or narrower comparison is welcome
only when it changes the question; no candidate count, architecture or positive answer is owed.
Cite consequential sources actually read and state decision-critical reading gaps honestly.

### Answer

**MATERIAL_DISSENT: no**。 我推荐的下一笔投入是 **C01 原定五个新配对块、十个 fit 的一次性条件程序均值确认**，不先购买移中心观察，不缩成一个“看符号再决定”的 pilot，也不在此刻结束这项具体确认机会。这是方向建议，不是运行接受或预算授予。

**决定性理由：** A2 在一个已经很有用的普通 U 对照之上，观察到同训练步数、同部署结构下约一名用户/步的额外服务；这个尺度值得区分“一个有利训练配对”与“固定评估条件下的正训练程序均值”。只有新训练块直接提供这一层信息。位置依赖可以与正条件均值同时成立，四中心固定策略观察的正负结果都不能替代这次区分。因此，它不是当前投资决定的必要前置诊断。

**最强反对理由也必须保留：** 约 7.43 小时买到的不是泛化机制、任意热点鲁棒性、下一次训练获益概率或实际采用保证，而是依赖五块小样本模型的零边际条件均值判断；它可能以很小的效应通过，也可能对实际有用的效应无力。这确实压低 C01 的价值，但结合下面的原生服务尺度、强对照和固定终止范围，我认为尚不足以改选停止。不能把“一个重要的不确定性尚存”本身当成继续训练的充分理由；这里值得付费的是一个有具体服务增量、可以被新训练否定其确认资格的有限学习问题。[实际 C01 草案][claim]已经主动排除了多数过宽承诺，我不以那些它没有提出的承诺为由反对它。

#### 1. A2 改变了哪些判断，哪些解释仍然活着

以下均是固定 U45/M45 在各自 32 个共同世界上的条件性读数，服务单位为用户/步。负世界指 J 或服务至少一项下降，不是独立训练失败率。

| 家族 | M−U 的 J | M−U 的服务 | 不利世界 | 最差 J / 服务差及世界 |
| --- | ---: | ---: | ---: | --- |
| hotspot，主留出生成器 | +.0185689864 | +.940750 | 12/32 | −.074145446 / −5.690；262020012 |
| uniform，原训练家族 | +.0090232920 | −.0000625 | 17/32 | −.067627130 / −5.442；262000008 |
| cluster，M 已见生成器 | +.0401648661 | +2.0878125 | 10/32 | −.069422559 / −5.266；262010028 |

这些均值、完整逐世界差和分量来自[原始批次汇总][batch]；[完成条目][a2result]同时保留原生核验、实际成本和存储范围。九个面板中的 J、服务及分量数组也已读取，而非只采信方向布尔值。

**加强的判断是“这一配对有留出增量”，不是“U 不会做这个任务”。** hotspot 上 U 相对真实初始化已经获得 J +.250359362、服务 +11.080438；M 自身为 +.268928349、+12.021188。uniform 的 U/M 自身服务增量分别为 +16.733000/+16.732938，cluster 为 +16.410063/+18.497875。两臂在每个世界的 J 都高于初始化，但 hotspot 自身服务仍有 U 的 −3.466（262020011）和 M 的 −.460（262020015）。因此，不能用 M 自身学习替代 M−U，也不能在新块中因为 U 学得太好或太差而筛掉它。[初始化与双方终点、完整自身学习][batch]

**削弱的是“收益只在见过的 cluster”和“有显著平均 uniform 服务牺牲才换来热点收益”这两个具体读法。** 但 uniform 接近零的样本均值不是等价、非劣或无局部损失；17 个服务损失世界仍在。hotspot 服务有 20 正、12 负，中位差 +1.285，最大差 +10.684，最差 −5.690；既不能只展示平均数，也不能把它说成只有一个挑中的正世界。cluster 的较大均值不能补做留出验证。[三家族完整差数组][batch]

**未识别的仍是作用原因及训练层面的稳定性。** hotspot 的资格增加 +2.264125，同时资格内未服务增加 +1.323375；两者之差才是 +.940750 服务。按原目标作代数分解，J 增量约为 coverage 项 +.013170500、quality 项 +.005344766、较低 height penalty 带来的 +.000053721。这不是因果中介分解，更不证明所有新增资格都可由某个容量或调度修复转成服务。S1 的该惩罚项是高度，不是实测电池风险。[原始分量][batch] 优化/训练随机性、训练布局与固定中心几何的交互、可重复但位置特定的策略偏好，都仍可解释观察；“固定中心机制已经诊断出来”没有依据。

#### 2. C01 的估计对象和配对是相称的，但它有意不回答更大的问题

令 W 为 C01 固定的新 hotspot 32 世界面板，R_b 为第 b 块的新初始化、训练世界及程序随机性；g_k 是 final45 在一个世界完整 H500 上的平均 J 或服务。实际主项可以写为：

$$d_{b,k}(W)=\frac{1}{32}\sum_{w\in W}\{g_k(M(R_b),w)-g_k(U(R_b),w)\},\qquad \mu_k(W)=\mathbb E_R[d_{b,k}(W)],\quad k\in\{J,S\}.$$

**五个 d 是单位，两个正的 mu 是主张。** 不是十个互不配对的臂，不是 160 个训练重复，不是 500 个时间步重复，也不是对所有未来热点世界积分后的总体均值。[C01 的 estimand、worlds 与 interval 规则][claim]

实际草案的 model seeds 263000101..105、块 b=0..4 的 training base 264000000+100000*b，以及 base+1000*r+lane 的世界地址，保留了新训练块与块内 U/M 配对。共享的是实际初始化和适当的共同外生条件，不是强求 uniform 与 cluster 产生同一物理世界。接受实现中的[世界与初始化代码][runner]、[原生布局适配器][adapter]与[冻结前瞻合同][prospective]都支持这种区分；M 的实际规则仍为 `(lane+r)%16<8`，每轮 8/8。应沿用后来纠正过的每 lane 21–24 次 uniform 暴露读法，不能复述初始说明的 22/23 算术错误。

共同初始化使完整程序差异可配对；其方差为 Var(M)+Var(U)−2Cov(M,U)，但没有证据保证这种耦合在所有新块中都强烈降低方差。跨块变化混合了初始化、训练世界及优化过程，不能单独叫作“初始化方差”。不同种子地址与实际隔离的随机流是设计基础，不是五个数足以验证独立同分布或正态性的证明。

所有块共享新的 uniform/cluster/hotspot 面板，分别从 265000000、265010000、265020000 开始，这**不是条件分析的伪重复**：给定 W，独立训练块仍可作为独立块；共享世界避免把每块不同评价难度混入块差。代价是区间不包含另抽 W 的不确定性。32 世界上的平均不能依靠中心极限定理替五个训练块建立 t 模型；政策级的共同变化不会因为一个政策多跑世界而消失。[C01][claim]

还有一个需要准确表述的边界：C01 相对 A2 同时换了训练块和评价世界。若 C01 未通过，不能据此唯一诊断“A2 是优化运气”，因为程序×面板交互也可能参与；若通过，也不能排除固定中心偏好。C01 是对**新固定面板上的程序均值**作确认，而不是给 A2 原配对的成因作归因。这不要求追加旧面板或更多中心，除非真正改了问题。

#### 3. 联合符号规则没有缺少多重校正的漏洞；五块 t 模型和功效才是实质风险

保留草案规定的两个边际双侧 95% Student-t 区间及 df=4：

$$L_k=\bar d_k-t_{.975,4}\frac{s_k}{\sqrt5}=\bar d_k-1.241664\,s_k.$$

两项下界都严格为正才支持联合主张。这里 t 的区间公式及覆盖率解释采用 [NIST 的均值置信限说明][nist]；以下阈值和情景数是据公式计算，不是新实验结果。

联合原假设是“mu_J≤0 **或** mu_S≤0”，成功事件是两个单侧拒绝事件的交集。因此，只要相应边际 t 检验有效，原假设成立时至少有一个真零假设，联合误报概率就不超过该边际的 .025；不需要假定 J 与服务独立，也不需要为了这个**全须通过**的符号主张再作 Bonferroni。另一方面，不能把两个边际双侧 95% 区间叫作联合 95% 同时覆盖区域。J 本来含有服务相关的 coverage 项，两个主指标也不是两份独立复制证据。

风险在于独立同分布、近似正态的块差工作模型。五块无法令人信服地检查偏斜、混合优化模态或稀有训练失败；正常性检验不显著也不能替它背书。用五块 bootstrap，或改做需要额外对称/交换性假设的符号翻转检验，不会自动补上这个缺口，更不应在看完结果后选一种能过的统计方法。

**A2 没有提供训练块差的方差，因此本项目的功效尚不能估计。** 32 个世界的离散程度和 12 个不利世界都不能拿来填这个训练层面的参数，B19/B20 也不能提供 A2 的重复样本。把旧点估计仅作为算术参考，若新五块均值恰好仍为 J .0185689864、服务 .940750，则要让相应下界大于零，样本标准差分别须小于约 **.014955 和 .757653 用户/步**。这只是给定样本均值的过线条件，不是充分功效论证。

进一步，仅在“真实服务均值=.940750、独立正态块差”的假设情景下，五块该正向拒绝规则在真实标准差 .5、.75、1.0 时的边际功效约为 .875、.565、.364（非中心 t 计算）。这些标准差不是从 A2 估出的；联合功效还不高于任何一个边际功效，不能凭未知的相关性直接相乘。**五块是一次可能留下不确定结论的有限购买，不是‘已设计到大概率成功’。**

我不建议把这点变成先补训练 pilot、事后重估样本量再延长的路线。那会改变当前固定暴露和停止承诺。若最终五块使 t 模型尤其难以相信，应保留全部块和约定计算、明确模型依赖，降低能承受的结论强度，而不是删块、换统计法或增加第六块。

#### 4. 为什么约一名用户的尺度仍值得这一次确认，但零边际不能代替实际用途

hotspot 的 U 服务为 23.241375，M 为 24.182125 用户/步；+.940750 相当于 50 名用户中的 **1.8815 个百分点**，约为 U 服务量的 **4.05%**。它是连续评价中的服务水平增量，不是每一步都额外服务同一个人，更不是新增唯一用户总数。最差 −5.690 的局部代价显著大于平均收益，不能藏掉。[原始读数][batch]

我的价值判断是：**在强普通 U 之上，不增加 actor 信息权限、网络结构、训练步数或推断调用结构，只替换一半训练经历，约这个量级的原生服务增量值得一次有限的训练层面确认。** 它不需要先证明机制或取得外部部署订单才成为基本研究事实。反过来，旧均值不到一人也不自动判为不实用；一人是可解释的尺度，不是来自需求的硬阈值。这里“同训练/推断”指固定结构和计数，不是假称两臂真实墙钟完全相等。

但零边际通过只回答“正”，不回答“足够大”。例如，新数据在模型下精确支持很小的正服务均值，形式主张可以通过，我仍不会据此主张全面采用 M 或继续购买同配方训练。也不能把下界大于零宣传为“至少多服务一人”；草案没有检验那个命题。无需为显得严格而临时编造一人 MEI 或 uniform 非劣界。

uniform 成本、cluster、自身学习和所有损失继续与主结果并列。它们不应事后被用作替代主项的成功门槛，却完全可以改变实际采用或后续投资判断。尤其是 uniform 出现明显服务损失时，hotspot 的统计通过不构成全面替换理由；若只 cluster 很好，也不能救活失败的 hotspot 联合主张。[实际 claim 的 secondary 与 practical-scale 边界][claim]

#### 5. 为什么不是更少训练块，也不是先做四中心 0-fit

**更少块不是没有信息，而是这里并不形成更划算的同一完整答案。** 新增一个配对约 1.49 小时能观察第二个训练实例，但仍不能有力估计程序差的离散程度；以其符号决定是否追加五块，会成为另一个有选择暴露的设计。不是不能研究单配对，而是不应把它当成 C01 的便宜等价物。

在相同样本标准差下，边际双侧 95% t 区间半宽和按旧运行线性外推的成本为：

| 新配对块数 | fits | 顺序墙钟参考 | 区间半宽 / s |
| --- | ---: | ---: | ---: |
| 3 | 6 | 4.46 h | 2.4841 |
| 4 | 8 | 5.95 h | 1.5912 |
| 5，C01 | 10 | 7.43 h | 1.2417 |

这不是预测各设计会有相同 s，也不是证明五块最优；它说明三块相对五块节省 40% 运行参考时间，却把同 s 的区间半宽约翻倍；四块节省 20%，半宽约增 28%。在增量本就不大、且准备固定终局读取而非继续追种子的情况下，我更愿意保留五块。**我把五块选为这里最小值得购买的完整确认，不声称它是统计学上可证明的最小样本量。** 不因宪章列有 3–5 个种子就自动购买任何一个数。

**四中心方案是一项合法但当前不改变选择的另一个问题。** 它让两份旧终点在 32 个新 base worlds 上接受同一组 35 个径向/角度抽样的中心平移，保留其余 15 名用户和 UAV 初态；四个 .35/.65 中心确实使半径 area/3 的圆盘留在边界内。重算 observation、state 和物理度量是必要的场景语义，不是只移动一个绘图标记。[锁定问题中的具体方案][question]

它的判别结果应精确读成：新中心之间出现配对增益反号，支持**这两份固定策略在这些条件上的位置依赖**；四处均正，削弱“正增量只在原中心这一处出现”这种很窄的猜想。两种结果都不提供新的训练重复，且都不能识别学习了某个中心机制或推出任意中心鲁棒性。保持 UAV 与其余用户不动，改变的是实际相对几何，不是整个场景的刚性平移等变性检验。

还有一个实际限制：四个新中心没有原来的 (.5,.5)。新中心之间可以作同一 base world 内的干净比较；若只是把某个新中心的负均值与旧 A2 中心的正均值相比较，中心与评价世界批次一起变了，不能把跨批次差异全部归给中心平移。无论如何，这不反驳原来的固定中心配对读数。

**对本次 C01 的投资决定，反号不会使其条件均值问题消失，同号也不会替它提供训练重复。因此我不购买这个观察作为筛选 C01 的前置步骤。** 只有研究问题真正改为“这两个现成策略在指定迁移位置的部署后果是什么”，它才可能成为最小有用观察；本轮没有这样的独立用途承诺，不默认用它拓宽或挽救 A2。

它确实是 0 fit，但仍有 128,000 评价团队步、256 episodes，及小型实现、场景核验、review、staging、收取和阅读。实际新墙钟未知。不能把 128k/4.32M 的步数比直接当墙钟或完整成本比，训练与冻结评价每步工作也不同。[具体替代方案及成本][question]

#### 6. 暴露、费用与固定失败规则：保留原计划，不附加救援

A2 的原 hotspot 主项本来就是前瞻指定的，不是从三个家族中事后挑出的胜者；但这次是否确认、对预期规模的认识，已经受 A2 正结果的选择影响。故旧 .940750 不能当作未来真实效应或可靠功效依据。C01 用全新训练和新评价地址、事前固定 final45 与联合规则、不池化 A2，正是隔离这段暴露的正确办法；它不抹掉选择历史，也不改善外部适用范围。[A2 原前瞻][prospective]；[C01 暴露约束][claim]

完整计划数应保留为 **3.6M training +720k evaluation=4.32M 团队步，25.92M UAV 行动行，10 fits、450 updates，actor 与 critic 各 1,012,500 次 optimizer calls**。A2 的科学过程为 U 2639.034 秒、M 2564.417 秒，批次科学墙钟 86.7289 分钟；89.1801 分钟是 admission-to-exit 的较宽口径。五对顺序外推为 7.431675 小时，原生文件量按旧批次五倍约 5.44 GB，另有核验副本。新争用、实现/支持和完整阅读不在这个墙钟保证之内。[U 原始 summary][usummary]；[M 原始 summary][msummary]；[批次 summary][batch]；[结束与存储记录][a2result]

我接受这个成本作为本次有限问题的相称参考，而非证明它胜过项目中所有其他用途的量化收益率；那些机会成本没有在材料中定价，不能编造。三轨 ceiling 也不是空闲算力或获得预算的证明。既有 [宪章][constitution]和[科学方法][methods]下，实际选择及独立发布仍属于 DM；本建议不增加预算审批层、额外 pilot、记录类型或跨任务联络。

最终读取应保持三种情况的区别。**两项下界都大于零：**只支持约定模型下该 W 的联合正条件均值，仍展示效应尺度、五个块和所有次要损失；通过本身不接受下一批。**任一不大于零：**联合主张未建立，既可能均值不利，也可能方差大而不确定；不给“等价”“无效”或“下一次一定失败”的结论，也不买第六块补救。**技术不完整：**保留 started fits、实际成本和缺失，不能缩成成功完成的若干块确认，更不能把技术失败解释为科学阴性。[C01 终止规则][claim]

即使统计通过，下一步也不是自动扩 seed、调比例或换 encoder。我建议把这批当成当前固定配方的终局确认读取：有用的有限正结论可以与不再购买同配方训练并存；未建立的结论也不要求用位置观察去救援。新的位置或机制问题要有它自己的科学理由，而不是既有正号的延长线。

#### 7. 对实际 claim/plan 的修订意见与读取边界

**没有要求更换主项、种子表、五块数、双侧 95% t 规则、零边际或停止规则的必要实质修订。** 特别不建议把 uniform 临时加成未定界的非劣主项、不建议改成五块全正才成功、不建议看到方差后追加块。草案已经说出的共享面板条件性、模型不保证、次要损失和不救援应完整保留。

可在原有解释文字中补清两句，不改变分析或设新门槛：“C01 结果不单独归因 A2 的正号来自优化随机性还是评价面板交互”；“零边际统计通过不等于约一人增量成立，也不自动构成替换 U 或继续同配方投资的理由”。这是避免读者把有限确认扩大为机制或采用结论，不是声称原稿已经犯了这些错误。

本答复以题定 `f3fb9bb6b0c5a6b49e2165113a35586a61f02f1c` 的问题、C01、宪章指定节和 scientific-tools 方法为主；共享理解使用明确指定的 `4fde2d73466fc80d91c3afbbbf0e3afc9f3ba8a1` 中 A2 coverage 段、standing 和 plan；既有建议只使用归档 Answer 第四、十一节的有关内容。B19/B20 不承担本次统计论证，也没有接管其工作。[指定共享理解][research]；[此前 A2 与改变优先级的建议][prior]

经验材料使用题定 source_sha 的完成条目，以及 `3453c67f1c9eb748300a4dca9746bf88e52119b9` 的原始批次及两臂 summary 相关字段，以及 **U stage00×三家族、U stage45×三家族、M stage45×三家族这九份面板的 J/分量/服务数组**；实现读取限于冻结 `d22b608e8d063ceac5c944426bd35a2289c5ebf6` 的 A2 adapter 与 runner 初始化/世界/配比部分，不宣称重审了整个依赖链。[U 六面板所在目录][udir]；[M 三面板所在目录][mdir]

**未读取的是 Git 外 native NPZ、训练 streams 和 checkpoints 的实际二进制内容；我读取了原发布者的哈希、计数及重建验收记录，没有亲自重算全部原生轨迹或加载模型。** 它限制的是本答复对运行完整性的独立核验强度，不把题面已接受的 A2 改成未完成。另有尚不存在/尚未知的新训练块差分布、真实功效、新执行墙钟和位置结果；不能用记忆或另一方向结果补全。没有未读的指定关键文本来源阻止上述方向建议。本轮没有进行训练、环境评价或实验实现。

**最终选择不变：保留 C01 五个新配对的一次性条件均值确认；不附带四中心前置诊断，不购买更小的符号 pilot，不扩大结论，也不承诺确认之后还有下一笔投资。MATERIAL_DISSENT: no。**

[claim]: https://github.com/CartmanFatass/My-paper-code/blob/f3fb9bb6b0c5a6b49e2165113a35586a61f02f1c/docs/research/candidates/spatial_demand_generalization/CLAIM_layout_coverage_conditional_mean_20260924.md
[question]: https://github.com/CartmanFatass/My-paper-code/blob/f3fb9bb6b0c5a6b49e2165113a35586a61f02f1c/docs/research/candidates/spatial_demand_generalization/NOTES.md#pro-question-2026-09-24-a2-replication-or-spatial-dependence
[prospective]: https://github.com/CartmanFatass/My-paper-code/blob/f3fb9bb6b0c5a6b49e2165113a35586a61f02f1c/docs/research/candidates/spatial_demand_generalization/NOTES.md#2026-09-24--direct-dm-adoption-and-a2-prospective-comparison
[a2result]: https://github.com/CartmanFatass/My-paper-code/blob/f3fb9bb6b0c5a6b49e2165113a35586a61f02f1c/docs/research/candidates/spatial_demand_generalization/NOTES.md#2026-09-24--a2-complete-modest-held-out-gain-and-heterogeneous-local-costs
[batch]: https://github.com/CartmanFatass/My-paper-code/blob/3453c67f1c9eb748300a4dca9746bf88e52119b9/runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101/summary.json
[usummary]: https://github.com/CartmanFatass/My-paper-code/blob/3453c67f1c9eb748300a4dca9746bf88e52119b9/runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101/U/summary.json
[msummary]: https://github.com/CartmanFatass/My-paper-code/blob/3453c67f1c9eb748300a4dca9746bf88e52119b9/runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101/M/summary.json
[udir]: https://github.com/CartmanFatass/My-paper-code/tree/3453c67f1c9eb748300a4dca9746bf88e52119b9/runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101/U
[mdir]: https://github.com/CartmanFatass/My-paper-code/tree/3453c67f1c9eb748300a4dca9746bf88e52119b9/runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101/M
[runner]: https://github.com/CartmanFatass/My-paper-code/blob/d22b608e8d063ceac5c944426bd35a2289c5ebf6/experiments/candidates/spatial_demand_generalization/a2/runner.py
[adapter]: https://github.com/CartmanFatass/My-paper-code/blob/d22b608e8d063ceac5c944426bd35a2289c5ebf6/experiments/candidates/spatial_demand_generalization/a2/adapter.py
[constitution]: https://github.com/CartmanFatass/My-paper-code/blob/f3fb9bb6b0c5a6b49e2165113a35586a61f02f1c/docs/project/OPERATING_CONSTITUTION.md
[methods]: https://github.com/CartmanFatass/My-paper-code/blob/f3fb9bb6b0c5a6b49e2165113a35586a61f02f1c/.agents/skills/hmasd-scientific-tools/SKILL.md
[research]: https://github.com/CartmanFatass/My-paper-code/blob/4fde2d73466fc80d91c3afbbbf0e3afc9f3ba8a1/docs/research/RESEARCH.md
[prior]: https://github.com/CartmanFatass/My-paper-code/blob/f3fb9bb6b0c5a6b49e2165113a35586a61f02f1c/docs/research/archive/2026-09-24/RESEARCH-question-led-programme-adopted.md
[nist]: https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm

## 2026-09-24 — C01 adopted: five fresh paired blocks, one fixed conditional-mean confirmation

**Decision and belief update.** I adopt the concrete C01 plan in
`CLAIM_layout_coverage_conditional_mean_20260924.md` unchanged: five fresh paired training
blocks, U then M in each, ten fits, final45 and the two predeclared marginal t95 lower bounds
both strictly positive. This is one fixed confirmation, not an extension of A2. A2 has already
ended with its complete result and contrary worlds preserved. About .94 more served users per
step above a strongly learning U, at unchanged training counts and deployment architecture,
is enough native value to justify this finite replication purchase. The new information is
the conditional training-program mean, not a mechanism or next-training reliability claim.
The same argument does not promise a next purchase after C01, even if it passes.

The shared training-coverage discussion at main
`4fde2d73466fc80d91c3afbbbf0e3afc9f3ba8a1` (RESEARCH, ordinary training coverage/A2 paragraphs)
remains the relevant background. It keeps the competent ordinary U, fixed LOCAL1 rights and
all original-family losses central, while separating training/layout coverage from partner
compatibility or causal support coverage. B19/B20 do not supply training replication for A2.
This preserves the exact comparator and selects fresh training blocks over an architecture
change. Current published pause is lifted, the lead is unchanged, and no new owner stop has
arrived; this direction keeps only this one result-bearing study within the three-track ceiling.

**Pro reading and response.** The one question key was
`hmasd:7fd87e60e0e6e62278905abf17cf75de575192127c36cd8e47d0d17447183d1e` at
source `f3fb9bb6b0c5a6b49e2165113a35586a61f02f1c`. Send was observed as sent with the complete
attachment. Native observation collected completion; the short chat text was a receipt-like
summary, not the scientific answer. Delivery independently verified commit
`ca77013402426ce5254ab260d688b651e3664178`, whose only change filled the empty Answer above:
question and every other byte unchanged. I read all 11,869 answer characters, including its
source-use limitations. The operation's tabs are closed (zero matching conversation tabs);
the private address remains solely in local transport state. Observation generation 6,
wake `af774582-831b-4bf7-836c-79ed5de7ec33`, event `444367c48c92619babe6f3a1` were consumed;
generation 7 has no remaining accepted observation to advance. No resend occurred.

Pro returned MATERIAL_DISSENT no and favored the actual five-pair plan. I accept its reason
that the four-center 0-fit observation cannot replace new training: a location-dependent gain
can coexist with either sign of the conditional training mean. Neither sign from those fixed
policies decides this investment. I therefore do not run that observation or a smaller
sign-screening pilot. Its extra caveat is useful: the proposed four-center panel omitted the
old center, so comparing it directly with A2 would confound center and new-world batch too.

The strongest objection survives adoption: roughly 7.43 hours purchases a five-block,
model-dependent, zero-margin result that may be too imprecise or too small for use. Five
blocks cannot establish normality, power, rare training-failure behavior, general hotspot
robustness, or the probability that the next training pair wins. No extra block, weak-U
filter, post-result interval selection or retry is justified by an unfavorable reading.
C01 changes the evaluation panel as well as training instances, so its result cannot uniquely
attribute A2's sign to optimization randomness versus program-by-panel interaction. A positive
zero-margin result would not establish an approximately one-user gain or justify replacing U.
These are adopted interpretation clarifications, not new success gates.

**Consequential claims checked.** I independently recomputed the t and noncentral-t arithmetic
with the existing scientific interpreter and checked the primary
[NIST mean-confidence-limit formula](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm).
For n5, t(.975,4)=2.7764451052 and half-width/s=1.2416639982. At the old point means, positive
lower bounds require sample SD below .0149549205 J and .757652635 users; these are arithmetic
conditions, not a power estimate. Conditional normal-model service-power scenarios for true
SD .5/.75/1.0 are .875248/.564911/.364145. No training variance is inferred from the 32 A2
worlds. The joint all-positive rule is an intersection of tests; under a true component null
its rejection probability is bounded by that marginal .025 if the working t assumptions hold.
This is not a simultaneous 95% interval claim, and correlated J/service are not independent
replications. Actual empirical A2 inputs were already reconstructed from native data; Pro
read published summaries/arrays but not the retained binaries and does not add an independent
native verification or any new training evidence.

**Fixed scope and cost.** Model seeds 263000101..105; block b training reset
264000000+100000*b+1000*r+lane; constructor 269900000+1000*b+lane. Shared fresh evaluation
worlds start 265000000/265010000/265020000 for uniform/cluster/hotspot, each 32 worlds H500.
The CLAIM fixes the full unchanged A2 algorithm/rights and all readings. Five pairs cost
3.6M training +720k evaluation =4.32M team steps /25.92M UAV rows, ten fits, 450 updates,
1,012,500 calls of each optimizer, 1,440 evaluation episodes. Five times A2's measured
5,350.806522 seconds is 7.431675725 hours; expected native files about 5,440,029,495 bytes
plus independently verified copies. New wall and support/reading costs are unmeasured.
This is a prospective estimate, not a time promise, fit allowance or entitlement.

**L0 implementation scope.** Deliver a C01 block runner and final five-block aggregation
under `experiments/candidates/spatial_demand_generalization/c01/`, its guarded entry
`scripts/run_spatial_demand_generalization_c01.py`, and focused tests under
`tests/experiments/candidates/spatial_demand_generalization/c01/`. Reuse frozen A2 code and
its dependency semantics without editing A2, shared learners, environments or launch tools.
The implementation may isolate A2's module-local configuration per invocation; it must not
leak mutable configuration between blocks or leave A2 default arm seeds bound accidentally.
Explicitly bind model/learner, private sampler, constructor, reset and evaluation seed paths;
persist C01 direction/object/block/seed/tag identity in configs, summaries and checkpoints,
and hash every actual source dependency including C01's entry and adapter/wrapper.

Publish all five blocks before the first result. Run one pair per native invocation, ordered
block 0..4, with fresh admission for each on the configured `wsl_4070` CPU/float32 host and
four torch threads. Tags are `s1_spatial_coverage_c01_b<b>_s<model-seed>`; each has its own
run root and accepted native handle. This topology keeps one direction study active and
allows resource admission between blocks; later blocks do not depend on earlier scores.
No aggregate scientific verdict until all five matching blocks are complete. The aggregator
must reject missing/duplicated/mismatched blocks and incompatible source/protocol/panels,
use five block means as units with df4, and retain all block/world/component/own-learning and
adverse readings. No pooling A2, substitute endpoint, alternate seed or resume path.

Required checks target changed behavior: real seed flow and common initialization within
blocks, independent streams across blocks, identical fixed physical evaluation panels,
unchanged A2 outputs for the same small technical configuration, exact production counts,
checkpoint/output identity, the admission-before-effects CLI, and missing/incorrect aggregate
inputs plus known-statistic interval cases. Technical fixtures use separate seeds/reduced
dimensions and never production evaluation addresses for learned-policy scores. Reuse A2's
passed real recurrent/storage and partial-failure evidence where unchanged. Obtain independent
review of seed binding, identity, CLI and statistical aggregation; the DM accepts the diff.
Only the named implementation/test/entry paths are delegated; NOTES, CLAIM, shared index,
Git index and launches remain DM-owned. Helpers launch no result-bearing work or children.
At this adoption entry, no C01 fit or evaluation has started. A technical failure preserves
its actual cost and incomplete fixed batch and triggers no automatic retry or replacement.

### C01 implementation accepted for configured-node verification

The fixed decision is published on main at `3889d40627612179188df21af7b1ee8018f69218`;
only this direction's standing, directly affected A2/C01 paragraph, plan and routing changed.
The temporary publication checkout was clean, durably published and reclaimed. Other leads,
pauses and directions are preserved. The original proposal's five blocks and rule are unchanged.

The Implementer returned four new C01-owned files. I read the code and focused tests and
accept the bounded implementation. It uses a fresh private A2 module namespace per block,
binding C01 seeds/identity and its checkpoint/JSON writer, with no changes to frozen A2 or
its shared dependencies. The offline aggregator requires all five complete production blocks,
same source/SHA, full exposure dictionaries and common actual physical panels; it reports
block-level t95 intervals and retains all per-world/component/own-learning readings.
During self-check, I required JSON-normalized spec comparison and mandatory initialization
identity fields, avoiding tuple/list mismatch and vacuous success on absent equality fields.
Those corrections and the corresponding refusal cases are in the final implementation.

Final local focused check: six tests passed in 12.63 seconds (14 upstream Pyparsing warnings).
The real reduced paths compare two independent technical blocks, paired U/M initialization,
distinct weights/private sampler state/RNG, shared evaluation geometry, and the unchanged A2
numerical path on the same technical inputs. Separate checks cover fixed seed/count arithmetic,
checkpoint/source identity, admission refusal/SHA mismatch before execution, and known t
arithmetic with missing/duplicate/failed/source-mismatched/physical-mismatched aggregation.
Statistical fixtures use synthetic scores only for software tests and the tracked native A2
JSON schema; they are not scientific observations. Each successful focused invocation performs
720 reduced technical training and 720 evaluation team steps across the real-path tests;
these are development checks with private addresses, not C01 production fits or extra n.

Independent Reviewer read the final diff and tests without duplicating their execution;
no material finding remained. Reviewed and DM-verified SHA256 bindings:

- C01 runner: `c9855ae98052ff4ffd5300399512ffffec82098375eaa34f08825ef6ce257899`.
- C01 entry: `07f38f923ea06c5f92b88cb6a7d5fa62faff67148439141650bf33b4b5e3ccf0`.
- C01 tests: `d74777b92940649184fe586a4f06fe30b1c3008da8be4dbcb82207259101c3ec`.
- C01 initializer: `85b4989ffad2104bc1c26c00e27c155a6347ba1c7623e3bb26e4084fa6a09ede`.

The actual-node authoring checkout is `/home/wu/hmasd-worktrees/spatial-c01-01a0d6ab`;
only committed source will be staged there and launched through a retained source snapshot.
Its sparse selection includes the tracked A2 compact JSON used by the schema test. The live
canonical research file was updated only in this direction's row, from current published main;
every other byte was checked unchanged, including its owner pause and other writers' work.
Node preparation initially stalled in a read-only Git promisor fetch from a plain SSH shell;
I terminated only that identified fetch tree before any policy write/worktree creation and
completed the same preparation through the configured network shell. No scientific process
was touched. The node's previously recorded bad-tree auto-GC and missing-object commit-graph
warnings remain unrepaired; source/worktree creation completed, and no history was rewritten.
Subsequent sparse materialization used only per-command Git cache/auto-GC settings. Actual-node
tests and fresh native admission remain the next checks; no C01 production fit has started.

## 2026-09-25 — C01 native checks and explicit pre-admission command repair

Published fixed input for **all five blocks** is
`9e44adde3d54fcd0363a2ebdbc1468494141c27b`. The configured wsl_4070 interpreter verified all
four reviewed file digests and passed the same six focused tests in **7.72 seconds** (14
upstream Pyparsing warnings). Source is unchanged after that check. Fresh published main
advanced to `5dda303f93` with this direction still confirming, the same lead and pause lifted.
No scientific choice, seed, endpoint or output changes.

The first outer supervisor delivery, `c01_b0_s263000101_9e44adde`, exited zero in its recorded
0-second duration without reaching native admission. Native status reported the expected
output absent; the exact C01 block tag had **no native claim**, and no matching kernel/runner
process existed. Its original wrapper, log, exit, PID and start record remain under
`/home/wu/.agent-tasks/c01_b0_s263000101_9e44adde`. Production cost is zero started fits and
zero environment steps, not a completed or failed training result.

The cause was reproduced without scientific effects: the configured supervisor joins its
command argv with `COMMAND="$*"` before eval, so passing zsh, -lic and its command as separate
arguments lost that command boundary. Zsh executed only `exec` and returned zero. An inert
printf test reproduced the zero/empty output; preserving the shell-quoted zsh invocation as
**one supervisor argument** returned the sentinel as expected. No launcher or supervisor code
is changed. I explicitly select this bounded invocation repair after reconciliation; it is
not an automatic restart or replacement of any accepted fit. The original native request has
not entered the admission kernel.

The corrected delivery will use a distinct outer task
`c01_b0_s263000101_9e44adde_native`, preserving the failed delivery's evidence, and the **same**
published source, native block-0 output, direction/lead, seed and admission identity. A kernel
claim found during reconciliation must be observed under that identity, never bypassed by a
new tag. The no-fit-retry/no-sixth-block confirmation rule remains unchanged. Only actual
native admission and observed runner identity will establish that C01 began.

### C01 block 0 accepted; same-handle native observation active

The Reviewer independently checked the installed supervisor and retained failed wrapper and
found no material objection to the explicit command-boundary repair. The corrected outer
delivery reached the unchanged native request. **Native admission accepted block 0 at
2026-09-25T07:05:10.526330Z**, at fixed source
`9e44adde3d54fcd0363a2ebdbc1468494141c27b`. Actual-node physical/effective available memory
was 15,005,155,328 bytes against the 4,294,967,296-byte floor; the kernel's fresh checks passed.
The failed outer delivery remains unchanged and is not a training attempt or native retry.

The [native manifest](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b0_s263000101/launch-manifest.json),
[preflight](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b0_s263000101/admission-preflight.json),
initial launch status and U config were copied from the node and byte/SHA256-matched.
Manifest SHA256 is `9cfc2e3b7d6219123667998229acf4e581c9c38128448c38e64c0286eff4a538`.
The actual U config identifies C01/block0/seed263000101, constructor269900000, training base
264000000 and the three shared 26500/26501/26502 evaluation prefixes as fixed above.

Accepted operation reference:
`/home/wu/projects/HMASD/.git/hmasd-admission/be72b81809bf6d81a05dce15db290f2848fac679a2f4fe850d1a9564a1d1df8c.json`.
Native outputs remain at
`/home/wu/hmasd-worktrees/spatial-c01-01a0d6ab/runs/spatial_demand_generalization/s1_spatial_coverage_c01_b0_s263000101`;
the retained source snapshot is
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/6dcb68c53a144a38bf330aed7f217329`.
Detailed node, process start identities, source and argv remain in the manifest. Status
confirmed consistent records and both supervisor/runner alive, with no exit witness.

The task-local deterministic observer is generation **8**, job
`spatial-c01-b0-s263000101`; its first observed fact at 07:06:46Z was accepted/running with
matching native identities. No pending event, error or stop was present. Earlier A2 and Pro
observations remain consumed. Checkpoints rearm this handle, never the outer supervisor or
scientific request. Subsequent blocks use the same fixed source and their own already-planned
seeds/tags after this pair terminates and is collected; they are not chosen by its scores.

An initial semantic check found U actually training: one started fit, one completed update,
8,000 recorded training team steps and 48,000 initialization-evaluation steps; M was
unstarted. This is progress only, not a result or confirmation verdict. Preserve the remote
authoring checkout at the fixed input while it owns live outputs; later notebook commits do
not require checking out over those untracked native files. Read and retain the whole pair
on completion, and apply the no-retry/incomplete-batch rule to any genuine technical failure.

### C01 block 0 checkpoint — 2026-09-25T07:31Z

Read the generation-8 checkpoint event `c1970404404e0aea8733a816` under wake
`4644e172-97bb-4e40-84c1-f368064e6f0b`. The 07:30:22Z native observation found the same
accepted claim, matching live supervisor/runner identities, consistent records and no exit
witness or observation error. No replacement scientific request was made.

At 07:31:39Z the native progress record showed U training at the rollout-32 update boundary:
256,000 training/stored team steps (1,536,000 UAV steps), 512 training episodes and 31
completed updates; one fit had started. Its three initialization panels accounted for
48,000 evaluation team steps, 96 episodes/resets, zero evaluation storage calls and zero
evaluation optimizer calls. Recorded U arm wall time was 1,509.750150632 seconds. M was
unstarted, failure was null and stderr was empty. These are intermediate progress counters,
not a completed arm, paired result or confirmation verdict.

Fresh published main `3ad84d020cf4b44b6dae0d317025b410148940d2` retained this direction's
confirming standing and lead and the lifted owner pause; the actual node also retained the
lifted pause. With no newer control change, the same accepted job
`spatial-c01-b0-s263000101` was rearmed to generation **9** for another 1,500-second bounded
observation window, consuming the event above. Fixed source, seeds, counts and decision rule
remain unchanged. No main/index update is needed for this checkpoint.

### C01 block 0 checkpoint — 2026-09-25T08:01Z

Read the sole pending generation-9 checkpoint event `9b2962f1d11c25b5ccb0d4fe`, wake
`653fb6cb-2b99-4e74-ac94-43b996dc06ab`. At 07:59:32Z the same accepted native operation
retained matching live supervisor/runner identities, consistent records and no exit witness
or observation errors. Earlier A2/Pro events remain consumed; no new Pro answer was pending.

At 08:01:25Z U's arm summary reported complete: 360,000 training/stored team steps,
2,160,000 training UAV steps, 720 episodes and 45 updates. Its six panels recorded 96,000
evaluation team steps, 576,000 evaluation UAV steps and 192 episodes/resets, with zero
evaluation storage/optimizer calls; arm wall time was 2,232.744182191 seconds. This is
technical arm progress, pending whole-pair evidence collection and scientific reading.

M's live arm summary reported one started fit and training at the rollout-20 update boundary:
160,000 training/stored team steps, 960,000 UAV steps, 320 episodes and 19 completed updates;
evaluation had not started. Recorded M arm wall time was 1,020.585341265 seconds. Both arm
failure fields were null; stderr was empty at 08:01:01Z. The batch summary still showed its
U-completion counts and M as running/fit_started=false; retain that snapshot distinction and
use M's own live record for these current progress counters. No paired effect or confirmation
verdict is available.

Fresh main remained `3ad84d020cf4b44b6dae0d317025b410148940d2`, with unchanged confirming
standing and lead and owner pause lifted; the canonical node pause was also lifted. Consumed
the checkpoint above and rearmed the same `spatial-c01-b0-s263000101` observation to
generation **10**, window 1,500 seconds. No worker restart, new launch, Pro resend, cross-task
message or main/index update was made.

## 2026-09-25 — C01 block 0 accepted: adverse J, near-zero hotspot service difference

The first of the fixed five paired blocks is fully collected and read. The native witness
records ordinary exit 0 at 2026-09-25T08:25:47.469621Z with the originally accepted process
identities. Generation-10 READY event `8c2c2e03bdcbdab67c9d751c`, wake
`6da59375-af45-468e-9241-22b575d713cc`, was consumed after this evidence reading (generation
11). Scientific acceptance below rests on the artifacts and reconstruction, not the exit code.

### Evidence and actual cost

Both U and M completed their fixed 360,000 training steps and 45 updates, with 101,250 actor
and 101,250 critic optimizer calls each. Total exposure is **two fits, 720,000 training plus
144,000 evaluation team steps, 5,184,000 UAV action rows**, nine evaluation panels and 288
evaluation episodes. Evaluation storage and optimizer calls are zero. Scientific wall was
4,674.513675 seconds (77.9086 minutes), U/M arm wall 2,232.744182/2,441.522985 seconds;
native admission to exit was 4,836.943655 seconds (80.6157 minutes). The process recorded
18,527.012349 user CPU seconds, 44.240376 system CPU seconds and peak RSS 1,839,288 KiB.
RSS is paired-process RUSAGE_SELF, excluding other processes; peak scratch was unmeasured.
Collection, verification and reading are additional costs and introduce no fit or evaluation.

All 23 actual source digests match fixed published input
`9e44adde3d54fcd0363a2ebdbc1468494141c27b`. Post-run reconstruction checked every one of the
144,000 evaluation transitions: unique-user/c10/eligibility constraints, service and unserved
counts from link matrices, coverage/quality/height components, native J against six times
scalar reward, executed clipping and state/observation continuity. All per-world metrics and
differences agree with the original summaries; maximum panel-J roundoff is 1.11e-15.
Initial physical scenes match within each family across the three evaluated policies.
All 90 training reset records retain their fixed seeds and family schedule; shared uniform
lanes match between arms. The four checkpoints carry the correct identity, and actual U/M
initial tensors and normalizers agree. All 90 training rows, 88 reset boundaries and recorded
evaluation preservation checks pass. Both native logs are empty. The read-only collector's
initial schema assumptions were corrected for cumulative training step counters and checkpoint
paths relative to the raw directory; original runner code and native evidence were unchanged.

The **136 original native files / 1,088,016,261 bytes** were copied from the recorded native
output, individually size/SHA256-checked, then independently copied and rechecked at
`/home/fires/hmasd-artifacts/spatial_demand_generalization/s1_spatial_coverage_c01_b0_s263000101`.
Canonical inventory SHA256 is `43dfd66fe93afd660f41055accff234b3df1a16923df8d97293ef8faa378fe5e`,
using the same ordered compact JSON definition as A2. Original batch summary SHA256 is
`9d350bde1d8dd69ec6223f2247bb7c08c25d644626829c4304bc51c11cffb3f8`.
The independent reading report is retained outside the checkout under
`/home/fires/hmasd-artifacts/spatial_demand_generalization/c01-postrun-reading/block0-verification.json`
(SHA256 `f55ea400e6c97ce31d8ba73b43d4e3a463e882aabb2b054eedcdd3ccaace35bf`), alongside its
read-only reader (SHA256 `187b51a47cce6435359383f92f3e51f56f6b63d66f25276568aebe47a5097f59`).
After verified retention, native snapshot GC preview and apply reclaimed only
`6dcb68c53a144a38bf330aed7f217329`; native outputs, claim, manifest and authoring checkout remain.
The documented read-only sudo process scan was used for the previously observed protected
process visibility requirement. No experimental process was restarted.

### Fixed per-block reading

Entries are native J / served users per step, averaged over all 32 fixed worlds per family.

| Family | Common initial | U45 | M45 | M45 minus U45 | Adverse J or service worlds |
| --- | --- | --- | --- | --- | --- |
| hotspot, primary | .229825258 / 15.459750 | .414168154 / 26.206250 | .399446957 / 26.214188 | **-.014721197 / +.007938** | 22/32 |
| uniform | .273289499 / 18.741938 | .532726414 / 34.601250 | .518171620 / 34.439813 | -.014554794 / -.161438 | 24/32 |
| cluster | .259819117 / 17.804625 | .511600493 / 32.797063 | .486909743 / 32.360563 | -.024690750 / -.436500 | 22/32 |

Both arms improve their own J and service in every evaluated world. Mean hotspot own-learning
gains are U +.184342896 J / +10.746500 service and M +.169621698 / +10.754438. Thus this
block's adverse paired J is not absence of learning by either program. Hotspot M-minus-U has
coverage +.000158750, quality -.012790460, height penalty +.010995184 (mean height +10.995184),
eligibility -1.866500 and eligible-but-unserved -1.874438. Fewer unserved eligible users alone
does not establish extra delivered service. Height penalty is not measured battery energy.

All 96 paired J/service world differences and all component/own-learning readings remain in
the [original batch summary](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b0_s263000101/summary.json).
The largest hotspot paired J and service losses coincide at seed 265020027:
-.082920548 J / -4.754 service. Uniform's largest J loss is seed 265000031 (-.076849165),
while its largest service loss is seed 265000027 (-4.144); cluster seed 265010004 loses
-.170850631 J / -11.888 service. These worlds remain in every reported mean.

This fresh block does not reproduce A2's joint positive direction. It is one of five planned
training units, not a population conclusion or a confirmation verdict. The new panel and new
training instance also prevent attribution of the sign change to either source alone.
Continue the already fixed block 1, seed 263000102, training base 264100000, constructor
269901000 and the same evaluation panels/input SHA. There is no endpoint, mixture, seed,
budget, stopping-rule or claim change. Fresh main `3ad84d020cf4b44b6dae0d317025b410148940d2`
retained the lead, confirming standing and lifted owner pause. This individual-block acceptance
is recorded on the direction branch; main/index publication remains at the material study boundary.

### C01 block 1 accepted; fixed study continues

Block-0 compact original evidence and the complete reading above are published on the
direction branch at `dec1ab78f`. The remote authoring checkout remains clean for tracked
inputs at the fixed C01 source; its retained block-0 native output was not checked out over.

The planned second pair, block 1 / model seed 263000102, received native admission at
**2026-09-25T08:38:04.165311Z**. The kernel observed current main
`3ad84d020cf4b44b6dae0d317025b410148940d2` and passed fresh actual-node resource admission:
13,997,506,560 physical/effective available bytes against the 4,294,967,296-byte floor.
The native [manifest and accepted operation reference](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b1_s263000102/launch-manifest.json)
and [preflight](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b1_s263000102/admission-preflight.json)
were copied with initial launch status and U config; all four byte counts and SHA256 values
match the executing node. Manifest SHA256 is
`a14b31d4447f1c9aeae46de747d8e2459c63835dd20e27cc48738ed4f6bcd4d9`.
Actual U configuration verifies constructor 269901000, training base 264100000 and the
unchanged fixed evaluation worlds. Input remains `9e44adde3d54fcd0363a2ebdbc1468494141c27b`.

Native status and the registered observer both saw the accepted operation running with
matching supervisor/runner identities, consistent records and no exit witness. At
08:38:59Z the same-handle observer `spatial-c01-b1-s263000102` was active at generation
**12**, window 1,500 seconds, with no errors or pending events. The completed block-0 event
remains consumed. This is the second prespecified pair in the one C01 study; no confirmation
verdict, additional block, revised claim or new scientific investment has been selected.

### C01 block 1 checkpoint — 2026-09-25T09:04Z

Read generation-12 checkpoint `b0e1297798d2ccf3479bf41c`, wake
`a793590e-6982-4b92-ab51-f30099a3fb34`. At 09:03:04Z the same accepted operation had matching
live supervisor/runner identities, consistent records, no exit witness and zero observer errors.
At 09:04:15Z U was training at the rollout-28 update boundary: 224,000 training/stored team
steps, 1,344,000 UAV steps, 448 episodes and 27 completed updates. Its three initialization
panels accounted for 48,000 evaluation team steps and 96 episodes/resets, with zero evaluation
storage/optimizer calls. U arm wall was 1,481.835082388 seconds; its failure field was null.
M was unstarted and stderr was empty. These are progress counters, not a second paired result.

Fresh main remained `3ad84d020cf4b44b6dae0d317025b410148940d2`, preserving the confirming
standing, lead and lifted owner pause; the canonical node pause was also lifted. Consumed the
checkpoint above and rearmed the same `spatial-c01-b1-s263000102` handle to generation **13**
for 1,500 seconds. Fixed inputs and decision rule remain unchanged; no worker, Pro request or
scientific launch was repeated, and no main/index update was made.

### C01 block 1 checkpoint — 2026-09-25T09:29Z

Read the sole pending generation-13 checkpoint `175775feaa759b8c6abee047`, wake
`04a10094-6da5-4643-b750-3e55bf7dd0fe`. The 09:28:41Z native observation retained the same
accepted claim, matching live process identities, consistent records, no exit witness and
zero observer errors. At 09:29:51Z U reported complete with 360,000 training/stored team
steps, 2,160,000 training UAV steps, 720 episodes and 45 updates. Its six panels account for
96,000 evaluation team steps and 192 episodes/resets; evaluation storage/optimizer calls
are zero. U arm wall was 2,367.842392656 seconds. Whole-pair collection and reading remain.

M's live arm record reported training at the rollout-14 update boundary: one started fit,
112,000 training/stored team steps, 672,000 UAV steps, 224 episodes and 13 completed updates;
no evaluation steps yet, arm wall 616.386184085 seconds. Both failure fields were null and
stderr was empty. The batch-level M fit flag remains its earlier boundary snapshot; current
progress above comes from M's live arm record, preserving that distinction.

Fresh main advanced to `66aed19c5e6df050f7bc5340be9127cf24bda9a9`. The relevant diff only
updates the S7 B10 result/next-question background and routing; this direction's lead,
confirming standing, pause and the shared constitution/compute controls are unchanged.
Both published and canonical-node owner pauses remain lifted. Consumed the checkpoint and
rearmed the same `spatial-c01-b1-s263000102` job to generation **14**, window 1,500 seconds.
No scientific conclusion, protocol change, new launch or main/index update follows this checkpoint.

## 2026-09-25 — Crash recovery and complete C01 block 1 reading

The owner reported a system crash and asked this task to continue. Generation 14 had no
pending event and retained an old 09:52:33Z running observation. Direct reconciliation of the
**same accepted operation** found a valid ordinary exit 0 at **09:56:32.188968Z**, with the
original supervisor/runner identities absent and consistent records. No worker, fit or Pro
question was restarted. Rearming only the observer produced generation-15 READY event
`ad1688dc76ae9df76f6f3eb4`, wake `fa79b208-c8b0-435c-845a-445ea34b1dda`; this was fully read
and consumed after artifact verification, advancing to generation 16.

### Local publication recovery

The crash left an empty object `3d2f7a36340ecb1a1a520909f729becf14c0347e` in the local shared
Git store. Fetch failed while validating another direction's branch reference. This task's
HEAD remains `649030b9bb5c5c677c7deae393cb4a723c802c9c`; its physical NOTES and the two
uncommitted checkpoint entries survived. Before further editing, the complete 96,555-byte
notebook was independently copied to
`/home/fires/hmasd-recovery/spatial-demand-01a0d6ab-20260925/NOTES-before-recovery.md`
(SHA256 `cb3156e98e64fd5867df601ff395ce9d6c5d1e136e420f80959f36a7f2e878b2`).

The shared damaged store and other branch references are preserved. Subsequent Git fetches
and publication use the independent owned checkout
`/home/fires/hmasd-recovery/spatial-demand-01a0d6ab-20260925/publication`, on the same
`codex/spatial-demand-generalization-a2` branch and existing published parent. The source
input commit is also independently retrievable there. Initial branch tracking in this
single-branch clone required adding this direction's exact fetch mapping; that local setup
was corrected without changing remote history. Current main was independently read at
`66aed19c5e6df050f7bc5340be9127cf24bda9a9`: owner pause lifted, same direction/lead/plan.
This is recovery of task-local publication, not a claim that the shared Git store is repaired.

### Evidence, retention and actual cost

The second fixed pair is scientifically accepted after reconstruction. Both arms completed
360,000 training steps and 45 updates, with 101,250 actor and critic optimizer calls per arm.
Actual total is **two fits, 720,000 training plus 144,000 evaluation team steps**, 5,184,000
UAV action rows, nine panels and 288 evaluation episodes; no evaluation storage or optimization.
Scientific wall was 4,529.081527 seconds (75.4847 minutes), U/M arm wall
2,367.842393/2,161.006548 seconds, and admission to exit 4,708.024017 seconds (78.4671 minutes).
Process user/system CPU was 18,065.071202/37.974791 seconds, process peak RSS 1,841,496 KiB;
other processes and peak scratch remain unmeasured. Recovery/collection/reading adds no fit.

The unchanged read-only reader checked all 23 source digests against the published input,
all 144,000 evaluation transitions and reconstructed metrics/differences, all 90 training
rows/reset records, 88 reset boundaries, four checkpoints and evaluation isolation. Maximum
panel-J roundoff was 1.44e-15; both native logs were empty. Actual U/M initialization agrees
within block. Across blocks 0 and 1, the physical initial evaluation panels are identical,
while initial model tensors and learner RNG digests differ at the declared model seeds.
After the crash, all 136 original block-0 files were also rehashed in both this checkout and
its independent durable copy against the pre-crash inventory: every size and digest matched.

The **136 original block-1 native files / 1,088,009,210 bytes** were copied and individually
verified against the node, then independently copied and rechecked at
`/home/fires/hmasd-artifacts/spatial_demand_generalization/s1_spatial_coverage_c01_b1_s263000102`.
Canonical inventory SHA256 is `1e351474cd3668c84fbae8ff30f27ce2d1361799e6423038c9650651c186a70e`;
original batch summary SHA256 is `fe1d96f2cfc08fad235711221bec2b4db5870f5ac110d6e756eefa6e49d09dd3`.
The durable `c01-postrun-reading/block1-verification.json` report has SHA256
`5495c448114c3c9991cbf85be66ffefa555aae589af1c928b3b5b15a82d56b5e`; the two-block/post-crash
integrity report there has SHA256 `42b22e680f3d8fd28698be089f9ba141e6a2c85742f6b605b6739c62a05bcb54`.
After retention, native snapshot GC preview and apply reclaimed only
`c44bc313bd554b54876055d02c1d549d`, with its claim, manifest, outputs and author checkout retained.

### Fixed per-block results and continuation

Values are native J / served users per step, averaging every one of the 32 fixed worlds.

| Family | Common initial | U45 | M45 | M45 minus U45 | Adverse J or service worlds |
| --- | --- | --- | --- | --- | --- |
| hotspot, primary | .113518372 / 12.189313 | .420736318 / 26.676438 | .440050533 / 28.158750 | **+.019314215 / +1.482313** | 9/32 |
| uniform | .167739278 / 16.141750 | .538818830 / 35.209438 | .551464282 / 35.733313 | +.012645452 / +.523875 | 15/32 |
| cluster | .134816294 / 13.738875 | .498273280 / 31.780750 | .524372283 / 33.864375 | +.026099004 / +2.083625 | 13/32 |

Both arms improve J and service from their common initialization in every evaluated world.
Hotspot own-learning changes are U +.307217946 J / +14.487125 service and M +.326532161 /
+15.969438. Hotspot M-minus-U components are coverage +.029646250, quality -.007868743,
height penalty -.000922463, eligibility -.714750 and eligible-but-unserved -2.197063.
All world differences, component readings and adverse cases remain in the
[original block summary](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b1_s263000102/summary.json).
Largest paired J/service losses coincide at hotspot seed 265020000 (-.095157101 / -7.196),
uniform seed 265000010 (-.053734432 / -4.646) and cluster seed 265010018 (-.074269624 / -5.090).

C01 now has **two of five complete paired blocks**, with opposite hotspot J contrast signs
on the same verified physical panel. This documents variation between the observed training
instances; it does not yet decide the conditional program mean. No partial-batch interval,
world-pooled training n, filtering or early confirmation verdict is used. Continue the fixed
third pair, block 2 / seed 263000103, training base 264200000 and constructor 269902000, at
the unchanged source, worlds, budget and five-block decision rule. The local crash did not
create a replacement fit or a new scientific investment decision.

### C01 block 2 accepted; observation restored

The crash-recovery record and complete block-1 compact evidence are published on the same
direction branch at `79a02989fe2fbe7c4759e7e27cbc00989bd58b51`, using the independent owned
publication checkout described above. A fresh fetch before this entry retained main
`da5344e044ed1ed381c58dfc7ade15774079231e`, the confirming standing, recorded lead and lifted
owner pause. Its relevant change from `66aed19c5e6df050f7bc5340be9127cf24bda9a9` concerns S7 B11
adoption/plans/routing; this direction's fixed protocol and shared controls remain unchanged.

The third prespecified pair, block 2 / model seed 263000103, received native admission at
**2026-09-25T10:15:19.058772Z**. The kernel observed that same current main and passed fresh
actual-node resource admission: 15,035,584,512 physical/effective available bytes against the
4,294,967,296-byte floor. The native
[manifest and accepted operation reference](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b2_s263000103/launch-manifest.json)
and [preflight](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b2_s263000103/admission-preflight.json)
were copied with initial launch status and U config; all four byte counts and SHA256 values
match the executing node. Manifest SHA256 is
`00d99af9d8531c7c189a409d0105d72bce002bb4f9fb64f540474db87648a3b1`.
Actual U configuration verifies constructor 269902000, training base 264200000, model seed
263000103 and the unchanged fixed evaluation worlds. Input remains
`9e44adde3d54fcd0363a2ebdbc1468494141c27b`; native outputs retain their existing author checkout.

Native status and the adopted observer both saw the accepted operation running with matching
supervisor/runner identities, consistent records and no exit witness. At
**2026-09-25T10:20:12.343999Z**, observer `spatial-c01-b2-s263000103` was active at generation
**17**, window 1,500 seconds, with zero errors and no pending event. Earlier completed events
remain consumed. The observer is a read-only status probe of this accepted handle; no worker
restart or Pro resend occurred. Two of five paired blocks have complete scientific readings;
the running third block is not another accepted result. No endpoint, seed, budget, decision
rule or claim changes follow this admission, and no per-block main/index update is made.

### C01 block 2 checkpoint — 2026-09-25T10:45Z

Read the sole pending generation-17 checkpoint `dec98280bbbccc621318c6a3`, wake
`542bcb79-6f07-4f2f-8d73-3d035830668f`. The 10:43:45Z native observation retained the same
accepted claim, matching live supervisor/runner identities, consistent records, no exit
witness and zero observer errors. At 10:45:29Z U's live arm record was at rollout 33's update
boundary: 264,000 training/stored team steps, 1,584,000 UAV steps, 528 episodes and 32 completed
updates. Actor and critic had each completed 72,000 optimizer calls. Its three initialization
panels account for 48,000 evaluation team steps and 96 episodes/resets, with zero evaluation
storage/optimizer calls and all recorded evaluation-isolation digests preserved. U arm wall
was 1,701.374959 seconds; the failure field was null. M was unstarted and stderr was empty.
The batch-level U fit flag remains its earlier boundary snapshot; these current counts come
from the live arm record. This is progress, not a complete third paired result.

Fresh main remained `da5344e044ed1ed381c58dfc7ade15774079231e`, retaining the confirming
standing, recorded lead and lifted owner pause; the canonical-node pause was also lifted.
Consumed the checkpoint and rearmed the same `spatial-c01-b2-s263000103` handle to generation
**18**, window 1,500 seconds. No worker restart, Pro resend, new launch, scientific conclusion
or main/index update follows this checkpoint.

The owner's intervening Git-status question prompted a read-only check of the original shared
store. The previously empty object `3d2f7a36340ecb1a1a520909f729becf14c0347e` was now 190 bytes
and readable as a commit, and the formerly unreadable branch tip was readable. Full
`git fsck --full --no-dangling` completed with exit 0 and no output. Thus the earlier statement
that the damage still remained was stale and was corrected to the owner; this task did not
perform the intervening repair and does not infer a hardware fault. The notebook agrees with
the publication copy, and the earlier retained C01 evidence checks remain recorded above.
Keep using the already established independent publication checkout without moving the
native author checkout or changing the accepted source and protocol.

### C01 block 2 checkpoint — 2026-09-25T11:11Z

Read the sole pending generation-18 checkpoint `a80041fd9b4cd5782575b02d`, wake
`6c53a6a0-38de-4df9-a4ac-9fdfeeddf3e1`. At 11:10:05Z the same accepted operation retained
matching live supervisor/runner identities, consistent records, no exit witness and zero
observer errors. At 11:11:22Z U reported complete: 360,000 training/stored team steps,
2,160,000 training UAV steps, 720 episodes, 45 updates and 101,250 actor/critic optimizer
calls each. Its six evaluation panels account for 96,000 team steps and 192 episodes/resets;
evaluation storage/optimizer calls remain zero, and all initial/final isolation flags are
preserved. U arm wall was 2,425.643046 seconds. Complete paired collection and reading remain.

M's live arm record was at rollout 16's update boundary: 128,000 training/stored team steps,
768,000 UAV steps, 256 episodes, 15 completed updates and 33,750 actor/critic optimizer calls
each. It had no evaluation transitions yet; arm wall was 788.632531 seconds. Both failure
fields were null and stderr was empty. The batch-level M fit flag is still its earlier
boundary snapshot; current progress above comes from the live arm record.

Fresh main remained `da5344e044ed1ed381c58dfc7ade15774079231e`; confirming standing, lead,
protocol and owner pause are unchanged, and the canonical-node pause is lifted. Consumed
this checkpoint and rearmed the same `spatial-c01-b2-s263000103` handle to generation **19**,
window 1,500 seconds. There is no worker restart, Pro resend, new launch, scientific verdict
or main/index change. Two of five paired blocks have complete scientific readings.

### C01 block 2 checkpoint — 2026-09-25T11:37Z

Read the sole pending generation-19 checkpoint `99b3cbb66bd9adb59d72c9a5`, wake
`b357457a-359f-48c2-a7a9-cd7ece8ef318`. The checkpoint observation at 11:35:53Z and direct
reconciliation at 11:37:14Z both retained the same accepted operation, matching live process
identities, consistent records and no exit witness; the observer had zero errors.

U's completed counts remain unchanged from the previous checkpoint. At 11:37:14Z M's live
record was at rollout 44's update boundary: 352,000 training/stored team steps, 2,112,000 UAV
steps, 704 episodes, 43 completed updates and 96,750 actor/critic optimizer calls each. No M
evaluation transitions had occurred yet. M arm wall was 2,254.098570 seconds; both failure
fields were null and stderr remained empty. The batch-level M fit flag still reflects its
earlier boundary snapshot; these progress counts come from the live arm record.

Fresh main remains `da5344e044ed1ed381c58dfc7ade15774079231e` with the same confirming standing,
lead, protocol and lifted pause; the canonical-node pause is also lifted. Consumed this
checkpoint and rearmed the same `spatial-c01-b2-s263000103` handle to generation **20**, window
1,500 seconds. No worker restart, Pro resend, new launch or scientific verdict was made.
Complete third-pair collection and reading are still pending; main/index is unchanged.

## 2026-09-25 — C01 block 2 complete: adverse paired results retained

The third fixed pair, model seed 263000103 at input
`9e44adde3d54fcd0363a2ebdbc1468494141c27b`, exited normally with code 0 at
**2026-09-25T11:39:19.017409Z**. Generation-20 READY event `6e43f2ef012838704c8c490e`, wake
`59d97f53-a86a-4e5c-bcf4-a951dfa054eb`, retained the original native identities, their absent
post-exit state, a valid exit witness and consistent records. Its
[manifest and operation reference](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b2_s263000103/launch-manifest.json)
remain the authority for the launch. The complete result is accepted after the evidence
reconstruction below; this does not decide the five-block confirmation claim.

### Integrity, retention and actual cost

All **136 original native files / 1,088,014,981 bytes** were copied and individually checked
against the executing node, then independently copied and rehashed at
`/home/fires/hmasd-artifacts/spatial_demand_generalization/s1_spatial_coverage_c01_b2_s263000103`.
The canonical inventory SHA256 is `9b44cd9520a1bc091a91913dd763d8635d93b391795a48bfa2b8ed0ae8652ff3`;
the original batch summary SHA256 is `57d9963761bb3114506c566b603a68c2d8ee41e2220354fa7a0cd220103ea962`.
Raw outputs remain outside Git; compact original JSON and this reading are published on the
direction branch. The durable `c01-postrun-reading/block2-verification.json` report has SHA256
`77fe5499a05107b29aa4e338f4c21fae66f105e775ba5fa1191a9e3ad1eacf56`; the three-block integrity report
there has SHA256 `7e5cee6c5957a3889cca584ed0dd7defd52a9f7d983f77936493039aec3d77c2`.

The unchanged read-only reader checked all 23 source digests against the published input,
all 144,000 evaluation transitions and reconstructed metrics/differences, all 90 training
rows/reset records, 88 reset boundaries, four checkpoints and evaluation isolation. Maximum
panel-J roundoff was 1.11e-15, and both native logs were empty. U/M initialization matches
within the pair. Physical initial evaluation scenes match blocks 0 and 1 for every family;
the actual initial model tensors and post-initialization RNG digest differ from both prior
blocks at the declared fresh seed. This is an integrity check, not additional training n.

Actual cost is **two fits, 720,000 training plus 144,000 evaluation team steps**, 5,184,000
UAV action rows, 90 updates, nine panels and 288 evaluation episodes. Each arm has 101,250
actor and 101,250 critic optimizer calls; evaluation storage and optimization are zero.
Scientific wall was 4,821.488311 seconds (80.3581 minutes), with U/M arm wall
2,425.643046/2,395.595983 seconds; admission to exit was 5,039.958982 seconds (83.9993 minutes).
Process user/system CPU was 19,323.603700/40.055437 seconds, and peak RSS was 1,838,916 KiB
within Linux RUSAGE_SELF. Other processes and peak scratch remain unmeasured. Collection and
read-only reconstruction add no fit. After verified retention and full reading, snapshot-GC
preview and apply reclaimed only `21aaa188de1c4b0a89f1012aca444f9e`, preserving the native claim,
manifest, outputs and author checkout. Consuming the READY event advanced observation to
generation **21**; no worker or Pro request was restarted.

### Native results and adverse worlds

Values are native J / served users per step, averaging all 32 fixed worlds in each family.

| Family | Common initial | U45 | M45 | M45 minus U45 | Adverse J or service worlds |
| --- | --- | --- | --- | --- | --- |
| hotspot, primary | .060253383 / 9.871875 | .382806631 / 25.401625 | .329926228 / 23.648813 | **-.052880403 / -1.752813** | 31/32 |
| uniform | .114896721 / 13.687563 | .520312359 / 34.587250 | .442533219 / 31.415813 | -.077779140 / -3.171438 | 32/32 |
| cluster | .092969299 / 12.023313 | .468799727 / 31.890000 | .411157147 / 29.120938 | -.057642580 / -2.769063 | 25/32 |

U improves its own J and service in every evaluated world. M improves its own J everywhere,
but its cluster service at seed 265010024 falls **2.324 users/step below its initialization**;
all other M own-service changes are positive. Both hotspot own-learning means are positive:
U +.322553248 J / +15.529750 service and M +.269672845 / +13.776938. Thus the paired disadvantage
does not mean an absence of mean learning by M; the own-service exception is retained.

Hotspot M-minus-U components are coverage -.035056250, quality +.000554198, height penalty
+.028507287, eligibility +.924563 and eligible-but-unserved +2.677375; mean height is +28.507287.
These are descriptive readings of the same pair, not a causal attribution. Height penalty
is not measured battery energy. J is lower for M in 31 hotspot, 32 uniform and 25 cluster
worlds; service is lower in 27, 31 and 23 worlds respectively. Largest paired J/service losses
coincide at hotspot seed 265020005 (-.099345781 / -4.654), uniform seed 265000029
(-.168564333 / -9.504) and cluster seed 265010024 (-.253994554 / -16.120). All 96 paired world
differences, components, own-learning readings and adverse cases remain in the
[original batch summary](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b2_s263000103/summary.json).
No world or block is removed.

C01 now has **three of five complete paired blocks**. This block is adverse for M on both
mean endpoints in every family, while observed block signs remain heterogeneous. Preserve
the fixed five-block rule without an interim interval, world-pooled training n, early claim
verdict or extra fit. Continue the prespecified fourth pair, block 3 / model seed 263000104,
training base 264300000 and constructor 269903000, at the unchanged source, fixed evaluation
worlds and budget. Main `da5344e044ed1ed381c58dfc7ade15774079231e` retains the same confirming
standing, lead and lifted owner pause. This block reading is published on the direction
branch; main/index publication remains at the material study boundary.

### C01 block 3 accepted; fixed fourth pair running

The complete block-2 evidence and adverse reading above are published at
`b37ce87421f4fb154f56b0b0c0025fbd32894d33`. Before dispatch, the native author checkout was
tracked-clean at the fixed C01 input, the planned block-3 output and outer task were absent,
and the canonical pause was lifted. The first status probe preceded native admission and
found no output reference; the same outer launch was reconciled through its manifest and
native status without another dispatch. Its short outer process exit is not the fit result.

Block 3 / model seed 263000104 received native admission at **2026-09-25T11:48:52.689422Z**.
The kernel read current main `da5344e044ed1ed381c58dfc7ade15774079231e` and passed fresh
actual-node resource admission: 14,987,096,064 physical/effective available bytes against the
4,294,967,296-byte floor. The native
[manifest and accepted operation reference](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b3_s263000104/launch-manifest.json)
and [preflight](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b3_s263000104/admission-preflight.json)
were copied with initial launch status and U config; all four byte counts and SHA256 values
match the executing node. Manifest SHA256 is
`04a2a75c77afb0e96e794ca03be42cb52e194a990360bea90489c1e244dff861`.
Actual U configuration verifies model seed 263000104, constructor 269903000, training base
264300000 and the unchanged evaluation worlds and algorithm settings. Accepted source stays
`9e44adde3d54fcd0363a2ebdbc1468494141c27b`; existing native outputs remain in the author checkout.

Native status and the adopted observer both saw the same accepted operation running with
matching supervisor/runner identities, consistent records and no exit witness. At
**2026-09-25T11:50:20.438150Z**, `spatial-c01-b3-s263000104` was active at generation **22**,
window 1,500 seconds, with zero errors and no pending events. All earlier completion events
remain consumed. A fresh publication-side fetch retained that same main and direction tip.
Three of five pairs have complete scientific readings; the fourth is running, with unchanged
protocol, budget and five-block decision rule. No worker restart or Pro resend occurred.

### C01 block 3 checkpoint — 2026-09-25T12:15Z

Read the sole pending generation-22 checkpoint `ead35aeaa9482a022590db5a`, wake
`ef93f402-ddaa-472c-9ad4-69a9c0782b44`. At 12:14:28Z the same accepted operation retained
matching live supervisor/runner identities, consistent records, no exit witness and zero
observer errors. At 12:15:39Z U's live arm record was at rollout 32's update boundary:
256,000 training/stored team steps, 1,536,000 UAV steps, 512 episodes, 31 completed updates
and 69,750 actor/critic optimizer calls each. Its three initialization panels account for
48,000 evaluation team steps and 96 episodes/resets, with zero evaluation storage/optimizer
calls and all recorded isolation flags preserved. U arm wall was 1,506.880065 seconds; the
failure field was null. M was unstarted and stderr was empty. The batch-level U fit flag
remains its earlier boundary snapshot; the progress above is from U's live arm record.

Fresh main advanced to `63e92fd69e7e1bed7365e93ae6c01fc80715dce9`. The relevant diff updates
S7 B11 results, shared interpretation, standing and routing. This direction's confirming
standing, lead and fixed plan are unchanged; the constitution and compute controls did not
change. Both published and canonical-node owner pauses remain lifted. Consumed the checkpoint
and rearmed the same `spatial-c01-b3-s263000104` handle to generation **23**, window 1,500
seconds. Three of five pairs have complete scientific readings; no new launch, worker
restart, Pro resend, scientific verdict or main/index update follows this checkpoint.

### C01 block 3 checkpoint — 2026-09-25T12:42Z

Read the sole pending generation-23 checkpoint `17b041d97dcfba0e94caa6d3`, wake
`6ffc1cf3-8d96-42cd-8033-f0c13c6e418f`. At 12:40:52Z the same accepted operation retained
matching live supervisor/runner identities, consistent records, no exit witness and zero
observer errors. At 12:42:03Z U reported complete: 360,000 training/stored team steps,
2,160,000 UAV steps, 720 episodes, 45 updates and 101,250 actor/critic optimizer calls each.
Its six evaluation panels account for 96,000 team steps and 192 episodes/resets; evaluation
storage/optimizer calls are zero, and all initial/final isolation flags are preserved.
U arm wall was 2,200.950139 seconds. Whole-pair collection and reading remain pending.

M's live arm record was at rollout 19's update boundary: 152,000 training/stored team steps,
912,000 UAV steps, 304 episodes, 18 completed updates and 40,500 actor/critic optimizer calls
each. It had no evaluation transitions yet; arm wall was 860.519234 seconds. Both failure
fields were null and stderr was empty. The batch-level M fit flag remains its earlier
boundary snapshot; these current counts come from the live arm record.

Fresh main advanced to `cb2afd9eae37529420539695ec11943de7f1a754`. Read the B20 completion and
shared interpretation: its joint claim is unestablished, with N7 adverse and N5 unresolved;
that other fixed confirmation does not change this accepted C01 protocol or provide a C01
verdict. This direction's standing, lead, pause and shared controls remain unchanged, and
the canonical-node pause is lifted. Consumed the checkpoint and rearmed the same
`spatial-c01-b3-s263000104` handle to generation **24**, window 1,500 seconds. No worker restart,
Pro resend, new launch, scientific verdict or main/index update follows this checkpoint.

## 2026-09-25 — C01 block 3 complete: fourth paired reading

The fourth fixed pair, model seed 263000104 at input
`9e44adde3d54fcd0363a2ebdbc1468494141c27b`, exited normally with code 0 at
**2026-09-25T13:04:30.805358Z**. Generation-24 READY event `129b151a55ea0dda258a001e`, wake
`4c1be2f7-b13d-4969-ae34-ad021434b663`, preserved the original accepted native identities,
their absent post-exit state, a valid ordinary exit witness and consistent records. The
[manifest and operation reference](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b3_s263000104/launch-manifest.json)
remain the launch authority. The complete paired result is accepted after the reconstruction
below; the fixed five-block confirmation remains incomplete.

### Integrity, retention and actual cost

All **136 original native files / 1,088,014,394 bytes** were copied and individually checked
against the executing node, then independently copied and rehashed at
`/home/fires/hmasd-artifacts/spatial_demand_generalization/s1_spatial_coverage_c01_b3_s263000104`.
The canonical inventory SHA256 is `7228d3946aa1ab4eb46cab7dfdc4f199e5c8b2cd045c5be73a20d66ed777fbed`;
the original batch summary SHA256 is `2c7c4fd319c43a752845f6add6f10908df3abaa518c77d2329bad8be26a4c2d8`.
Raw outputs remain outside Git; compact original JSON and this reading are published on the
direction branch. Durable reports under
`/home/fires/hmasd-artifacts/spatial_demand_generalization/c01-postrun-reading/` include
`block3-verification.json` (SHA256 `522a82447467339aa0c45d2458d2b52309add390ebf5380f8399e1c817bf1603`),
`block3-collection.json` (`31e0731313bd0494883330f14d5c9799dafb0931364bbecbdc21156f40a7814a`) and
`blocks0-3-integrity.json` (`18d91af22997a54e59ee9742c91f5c298c9f07c80d9c0714a57374e7d4999f29`).

The unchanged read-only reader checked all 23 source digests against the published input,
all 144,000 evaluation transitions and reconstructed metrics/differences, all 90 training
rows/reset records, 88 reset boundaries, four checkpoints and evaluation isolation. Maximum
panel-J roundoff was 1.5544e-15, and both native logs were empty. U/M initialization matches
within the pair. Physical initial evaluation scenes match all three earlier C01 blocks in
every family; actual initial model tensors and the post-initialization RNG digest differ
from each prior block at the declared fresh seed. This checks integrity, not extra training n.

Actual cost is **two fits, 720,000 training plus 144,000 evaluation team steps**, 5,184,000
UAV action rows, 90 updates, nine panels and 288 evaluation episodes. Each arm has 101,250
actor and 101,250 critic optimizer calls; evaluation storage and optimization are zero.
Scientific wall was 4,358.313915 seconds (72.6386 minutes), with U/M arm wall
2,200.950139/2,157.130611 seconds; admission to exit was 4,538.116310 seconds (75.6353 minutes).
Process user/system CPU was 17,410.738582/37.659281 seconds, and peak RSS was 1,843,748 KiB
within Linux RUSAGE_SELF. Other processes and peak scratch remain unmeasured. Collection and
read-only reconstruction add no fit. After verified retention and full reading, snapshot-GC
preview and apply reclaimed only `b2bbb97709af4cb7bcc58517003c7ad4`, preserving the native claim,
manifest, outputs and author checkout. Consuming the READY event advanced observation to
generation **25**; no worker or Pro request was restarted.

### Native results and adverse worlds

Values are native J / served users per step, averaging all 32 fixed worlds in each family.

| Family | Common initial | U45 | M45 | M45 minus U45 | Adverse J or service worlds |
| --- | --- | --- | --- | --- | --- |
| hotspot, primary | .076775559 / 10.289813 | .401547886 / 25.029375 | .385682646 / 23.533938 | **-.015865239 / -1.495438** | 23/32 |
| uniform | .137504650 / 14.654188 | .534503484 / 34.117188 | .513169355 / 32.551750 | -.021334129 / -1.565438 | 27/32 |
| cluster | .106018374 / 12.306000 | .470652086 / 29.588313 | .465786166 / 28.980625 | -.004865920 / -.607687 | 19/32 |

Both U and M improve their own J and service in every evaluated world. Hotspot own-learning
means are U +.324772327 J / +14.739563 service and M +.308907088 / +13.244125. Uniform
own-learning means are U +.396998834 / +19.463000 and M +.375664705 / +17.897563; cluster
means are U +.364633712 / +17.282313 and M +.359767793 / +16.674625. Thus this pair's M-versus-U
disadvantage coexists with positive own learning, and neither result is discarded.

Hotspot M-minus-U components are coverage -.029908750, quality +.004626167, height penalty
-.003683035, eligibility -1.362063 and eligible-but-unserved +.133375; mean height is
-3.683035. These are descriptive readings of the same pair, not a causal attribution;
height penalty is not measured battery energy. J is lower for M in 22 hotspot, 26 uniform
and 18 cluster worlds; service is lower in 23, 26 and 19 worlds respectively. The largest
paired J/service losses coincide at hotspot seed 265020008 (-.103973582 / -7.680) and uniform
seed 265000027 (-.081291006 / -6.092). Cluster's largest J loss is seed 265010004
(-.121016636 J / -8.556 service), while its largest service loss is seed 265010030
(-.117083597 / -9.558). All 96 paired world differences, components, own-learning readings
and adverse cases remain in the
[original batch summary](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b3_s263000104/summary.json).
No world or block is removed.

C01 now has **four of five complete paired blocks**. This block has lower M means on both
endpoints in every family. Preserve the fixed five-block rule without an interim interval,
world-pooled training n, early claim verdict or extra fit. Continue the prespecified final
pair, block 4 / model seed 263000105, training base 264400000 and constructor 269904000,
at the unchanged source, evaluation worlds and budget.

Fresh main is `a2b074546db70db5062bb418c295f97abd9ac351`. Read its complete relevant diff:
the other DM has ended the ordered-mixing investment, declined further panel replay and
selected C2's separate fixed-policy sending comparison. That evidence does not change the
accepted C01 protocol or supply its confirmation verdict. This direction's confirming
standing, lead and controls are unchanged; published and canonical-node owner pauses remain
lifted. This block reading is published on the direction branch using the independent owned
publication checkout; main/index publication remains at the material study boundary.

### C01 block 4 accepted; fixed final pair running

The complete block-3 evidence and adverse reading above are published at
`435764021e8582964527ae261ad30e49c4371c2f`. Before dispatch, the native author checkout was
tracked-clean at the fixed C01 input, the planned block-4 output and outer task were absent,
and the canonical pause was lifted. There was one outer dispatch, followed by native
admission reconciliation; no existing operation was restarted.

Block 4 / model seed 263000105 received native admission at **2026-09-25T13:15:55.880728Z**.
The kernel read current main `a2b074546db70db5062bb418c295f97abd9ac351` and passed fresh
actual-node resource admission: 15,201,566,720 physical/effective available bytes against
the 4,294,967,296-byte floor. The native
[manifest and accepted operation reference](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b4_s263000105/launch-manifest.json)
and [preflight](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b4_s263000105/admission-preflight.json)
were copied with initial launch status and U config; all four byte counts and SHA256 values
match the executing node. Manifest SHA256 is
`32e26e0744220173acae02a024e922796769b1e9f3d7abcd88d8765ff6480718`.
Actual U configuration verifies model seed 263000105, constructor 269904000, training base
264400000 and the unchanged evaluation worlds and algorithm settings. Comparing with the
prior arm's configuration found only the prescribed seed changes. Accepted source stays
`9e44adde3d54fcd0363a2ebdbc1468494141c27b`; existing native outputs remain in the author checkout.

Native status and the adopted observer both saw the same accepted operation running with
matching supervisor/runner identities, consistent records and no exit witness. At
**2026-09-25T13:16:36.917840Z**, `spatial-c01-b4-s263000105` was active at generation **26**,
window 1,500 seconds, with zero errors and no pending events. All earlier completion events
remain consumed. A fresh publication-side fetch retained that same main and direction tip.
Four of five pairs have complete scientific readings; the fifth is running, with unchanged
protocol, budget and five-block decision rule. No worker restart or Pro resend occurred.

### C01 block 4 checkpoint — 2026-09-25T13:41Z

Read the sole pending generation-26 checkpoint `c02b2ad97a8b90fbf8df8b52`, wake
`30a73974-e093-4b7c-8cf8-0e75dfb1c4ef`. At 13:40:14Z the same accepted operation retained
matching live supervisor/runner identities, consistent records, no exit witness and zero
observer errors. At 13:41:49Z U's live arm record reported 248,000 training/stored team
steps, 1,488,000 UAV steps, 496 episodes, 30 completed updates and 67,500 actor/critic
optimizer calls each. Its three initialization panels account for 48,000 evaluation team
steps and 96 episodes/resets; evaluation storage/optimizer calls are zero, and all recorded
initial-stage isolation flags are preserved. U arm wall was 1,449.213197 seconds and its
failure field was null. M was unstarted; both native logs were empty. These progress counts
come from the live U record, not the batch's earlier boundary snapshot. The pair remains
running and is not yet scientifically accepted.

Fresh main advanced to `c41a10c21ed6d1722c84fc813c3e2c4718684129`. Read the complete relevant
diff: C2's engineering is accepted and its owner-specific control-row restriction remains
pending. This direction's confirming standing, lead, fixed plan, constitution and compute
controls are unchanged. Both published and canonical-node owner pauses remain lifted.
Consumed this checkpoint and rearmed the same `spatial-c01-b4-s263000105` handle to
generation **27**, window 1,500 seconds. Four of five pairs have complete scientific
readings; no new launch, worker restart, Pro resend, scientific verdict or main/index
update follows this checkpoint.

### C01 block 4 checkpoint — 2026-09-25T14:07Z

Read the sole pending generation-27 checkpoint `2c466dc9405bef50400e0b79`, wake
`758f625a-4adf-4fc8-81d9-2f3571bce18f`. At 14:06:23Z the same accepted operation retained
matching live supervisor/runner identities, consistent records, no exit witness and zero
observer errors. At 14:07:59Z U reported complete: 360,000 training/stored team steps,
2,160,000 UAV steps, 720 episodes, 45 updates and 101,250 actor/critic optimizer calls each.
Its six evaluation panels account for 96,000 team steps and 192 episodes/resets; evaluation
storage/optimizer calls are zero and all recorded initial/final isolation flags are preserved.
U arm wall was 2,184.306805 seconds. Whole-pair collection and scientific reading remain pending.

M's live record was at rollout 17's update boundary: 136,000 training/stored team steps,
816,000 UAV steps, 272 episodes, 16 completed updates and 36,000 actor/critic optimizer
calls each. It had no evaluation transitions yet; arm wall was 748.047404 seconds. Both
failure fields were null and both native logs were empty. These progress counts are from
the live arm records rather than the batch's earlier boundary snapshot.

Fresh main advanced to `0f4b705dc322fa9866b29c670166ba6293e4de07`. Read the complete relevant
diff: the separate C2 B01 comparison is complete and preserves RR, with FAST_ONLY adverse
despite shorter transit and lower attempt cost; its pending/history/age changes do not
identify a pure content mechanism. This does not alter the accepted C01 protocol or decide
its claim. This direction's standing, lead, fixed plan, constitution and compute controls
are unchanged; published and canonical-node owner pauses remain lifted. Consumed this
checkpoint and rearmed the same `spatial-c01-b4-s263000105` handle to generation **28**,
window 1,500 seconds. Four of five pairs have complete scientific readings; no new launch,
worker restart, Pro resend, scientific verdict or main/index update follows this checkpoint.

## 2026-09-25 — C01 block 4 complete: final paired evidence retained

The fifth fixed pair, model seed 263000105 at input
`9e44adde3d54fcd0363a2ebdbc1468494141c27b`, exited normally with code 0 at
**2026-09-25T14:31:23.256248Z**. Generation-28 READY event `cbc3f6d44d70a497a59b3884`, wake
`89a07e01-3a64-40d9-bd2e-f2fbf0055bde`, retained the original accepted native identities,
their absent post-exit state, a valid ordinary exit witness and consistent records. The
[manifest and operation reference](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b4_s263000105/launch-manifest.json)
remain the launch authority. This pair is scientifically accepted after the full reading below.

### Integrity, retention and actual cost

All **136 original native files / 1,088,016,909 bytes** were copied and individually checked
against the executing node, then independently copied and rehashed at
`/home/fires/hmasd-artifacts/spatial_demand_generalization/s1_spatial_coverage_c01_b4_s263000105`.
Canonical inventory SHA256 is `28c08574b1580f0c9bea2dadc19e9e839c17ce9470065ba5e911a06822ed3ca7`;
the original summary SHA256 is `64993678657301c8cba111197087979e4b004a94adfbd99027178294efbd909e`.
The unchanged read-only reader checked all 23 source digests, 144,000 evaluation transitions,
90 training rows/reset records, 88 reset boundaries, four checkpoints, metric reconstruction
and evaluation isolation. Maximum panel-J roundoff was 1.4989e-15; both native logs were empty.
Within-pair initialization matches. Actual physical initial evaluation scenes match all four
earlier blocks; initial model tensors and post-initialization RNG differ from each earlier
block. Source bytes remain those of the accepted input.

Durable reports in `/home/fires/hmasd-artifacts/spatial_demand_generalization/c01-postrun-reading/`
are `block4-verification.json` (SHA256
`f8803b5f8c5f7e1fd11edbbc0697491fd4402a884233e566ab8b223359642ec5`),
`block4-collection.json` (`af125d2b3dde5f13a9eccbfc02dbd1fb9d349e4f7dd59510d3d383d1f75f61c5`) and
`blocks0-4-integrity.json` (`23d076d25772a87fd6152e0d1c0d54c0e467aaab35069bea4d2ae4b326474858`).
Raw files remain outside Git; compact original JSON and this reading are published unchanged.

Actual cost is two fits, 720,000 training plus 144,000 evaluation team steps, 5,184,000 UAV
action rows, 90 updates, nine panels and 288 evaluation episodes. Each arm has 101,250 actor
and 101,250 critic optimizer calls; evaluation storage and optimization are zero. Scientific
wall was 4,302.471504 seconds (71.7079 minutes), with U/M arm wall 2,184.306805/2,117.931727
seconds; admission to exit was 4,527.375832 seconds (75.4563 minutes). Process user/system
CPU was 17,375.032377/36.360711 seconds, and peak RSS was 1,840,372 KiB within RUSAGE_SELF.
Other processes and peak scratch remain unmeasured. After verified retention and full reading,
snapshot-GC preview and apply reclaimed only `0640dc084682484ab7d1833e7e20f9d3`, preserving
native claim, outputs and author checkout. Consuming READY advanced observation to generation
**29**; all five C01 native operations are complete, with no worker or Pro request restarted.

### Native results and adverse worlds

Values are native J / served users per step over all 32 fixed worlds per family.

| Family | Common initial | U45 | M45 | M45 minus U45 | Adverse J or service worlds |
| --- | --- | --- | --- | --- | --- |
| hotspot, primary | .197685995 / 14.752063 | .402396680 / 25.558625 | .338386841 / 21.360875 | **-.064009839 / -4.197750** | 27/32 |
| uniform | .207615475 / 15.926688 | .532502780 / 34.596312 | .495952357 / 32.652000 | -.036550424 / -1.944312 | 26/32 |
| cluster | .195827047 / 15.202625 | .502064859 / 32.483313 | .413800835 / 26.852250 | -.088264024 / -5.631063 | 28/32 |

Both arms improve their mean J and service in every family. U improves both in every world.
M's own-service exceptions are uniform 265000026 (-1.340 users/step), cluster 265010027
(-4.038), hotspot 265020009 (-1.602) and 265020012 (-3.042); cluster 265010027 also has its
only own-J loss, -.023944508. These are preserved beside positive own-learning means.
Hotspot own means are U +.204710685 J / +10.806562 service and M +.140700846 / +6.608812.

Hotspot M-minus-U components are coverage -.083955000, quality -.010414995, height penalty
+.002116841, eligibility -3.686312 and eligible-but-unserved +.511438; height is +2.116841.
This is a descriptive decomposition, not causal attribution or measured battery energy.
J is lower for M in 27 hotspot, 26 uniform and 28 cluster worlds; service is lower in 25,
24 and 28 respectively. The largest paired J/service losses coincide at hotspot 265020011
(-.209699959 / -14.314), uniform 265000026 (-.204191854 / -13.492) and cluster 265010027
(-.303702695 / -20.008). All 96 differences, own-learning cases and components remain in the
[original summary](../../../../runs/spatial_demand_generalization/s1_spatial_coverage_c01_b4_s263000105/summary.json).
No block, world or endpoint is replaced or excluded.

## 2026-09-25 — C01 complete: joint positive mean not established

**Fixed result.** All five fresh paired blocks and all ten fits are complete and accepted.
Under the prewritten df4, marginal two-sided t95 rule, the joint positive hotspot J/service
claim is **not established**. Both point estimates are adverse, while both intervals span
zero: this is an imprecise conditional mean result with adverse observations, not equivalence,
a confirmed negative population effect or technical incompleteness. The exact five-block
confirmation ends here; there is no sixth block, substitute seed, chosen endpoint or retry.

The frozen `aggregate_five_blocks` from input `9e44adde3d54fcd0363a2ebdbc1468494141c27b`
read all five accepted original summaries. Its code hash is
`c9855ae98052ff4ffd5300399512ffffec82098375eaa34f08825ef6ce257899`. Its guards passed source,
identity, count, configuration, endpoint and shared-physical-panel checks. Independent NumPy
reconstruction from the transition-verified block readings and SciPy's df4 t quantile matched
all 24 metric intervals. This is post-run arithmetic with zero new policy/environment calls.
The [complete aggregate](../../../../runs/spatial_demand_generalization/c01_five_block_confirmation_20260925/summary.json)
has SHA256 `904cf37507b7cc8c83d74d0c95797dd975db5c70740e04ee3dcffa0e612d453a`;
[reading provenance and actual costs](../../../../runs/spatial_demand_generalization/c01_five_block_confirmation_20260925/reading.json)
have SHA256 `3c006c1a757021ae6c48ce0969cf3924dbd4053bfdc77dd250682e4b2dae96b2`.
Both have verified independent copies under
`/home/fires/hmasd-artifacts/spatial_demand_generalization/c01_five_block_confirmation_20260925/`.

### All five paired effects and fixed uncertainty

Each entry is a mean over the same 32 worlds, in native J / served users per step. The five
training-block differences, not the 160 world rows or the ten separate arms, are the units.

| Block / model seed | Hotspot M-U | Uniform M-U | Cluster M-U | Adverse worlds H / U / C |
| --- | --- | --- | --- | --- |
| 0 / 263000101 | -.014721197 / +.007938 | -.014554794 / -.161438 | -.024690750 / -.436500 | 22 / 24 / 22 |
| 1 / 263000102 | +.019314215 / +1.482312 | +.012645452 / +.523875 | +.026099004 / +2.083625 | 9 / 15 / 13 |
| 2 / 263000103 | -.052880403 / -1.752813 | -.077779140 / -3.171438 | -.057642580 / -2.769063 | 31 / 32 / 25 |
| 3 / 263000104 | -.015865239 / -1.495438 | -.021334129 / -1.565438 | -.004865920 / -.607687 | 23 / 27 / 19 |
| 4 / 263000105 | -.064009839 / -4.197750 | -.036550424 / -1.944312 | -.088264024 / -5.631063 | 27 / 26 / 28 |

| Family / endpoint | Mean M-U | Sample SD | Two-sided marginal t95 interval | Positive / zero / negative blocks |
| --- | --- | --- | --- | --- |
| **Hotspot J, primary** | **-.025632493** | .033353903 | **[-.067046834, +.015781848]** | 1 / 0 / 4 |
| **Hotspot service, primary** | **-1.191150** | 2.123258803 | **[-3.827524015, +1.445224015]** | 2 / 0 / 3 |
| Uniform J, secondary | -.027514607 | .033268434 | [-.068822823, +.013793609] | 1 / 0 / 4 |
| Uniform service, secondary | -1.263750 | 1.466641423 | [-3.084825853, +.557325853] | 1 / 0 / 4 |
| Cluster J, secondary | -.029872854 | .044625487 | [-.085282714, +.025537006] | 1 / 0 / 4 |
| Cluster service, secondary | -1.472138 | 2.891450216 | [-5.062347136, +2.118072136] | 1 / 0 / 4 |

Primary J range is [-.064009839, +.019314215]; service range is [-4.197750, +1.4823125].
The fixed t critical value is 2.7764451051977987. Neither lower bound is positive; neither
upper bound is negative. The service interval contains both zero and the declared approximately
one-user reference scale, as well as substantial loss. Thus the data neither establish the
positive mean nor rule out a one-user gain under the working model. No post-result margin,
equivalence test, world bootstrap, alternate interval or A2 pooling is introduced. Shared
fixed worlds condition this inference; five blocks do not establish iid-normal validity,
power, arbitrary-layout robustness or next-training reliability. The two marginal intervals
are not a simultaneous 95% region and the correlated endpoints are not independent replications.

### Own learning, components and working explanation

All ten fits have positive mean own J and service in all three families, with nonzero actor
and critic parameter movement and the declared updates. Across five blocks, hotspot common
initial / U45 / M45 averages are .135611713 / .404331134 / .378698641 J and
12.512563 / 25.774463 / 24.583313 served users. U and M own-learning means are respectively
+.268719420 / +13.261900 and +.243086928 / +12.070750. Uniform own means are U
+.351563649 / +18.791863 and M +.324049042 / +17.528113; cluster own means are U
+.332388063 / +17.492800 and M +.302515209 / +16.020663. Own learning does not substitute
for incremental benefit. U has no own-J/service loss on these worlds; M's one own-J and five
own-service exceptions across the batch are retained in the block-2 and block-4 readings.

Across-block hotspot M-U means are C -.023823000, Q -.005178767, P +.007402763,
eligibility -1.341013, eligible-but-unserved -.149863 and height +7.402763. The J identity
is .7C+.3Q-P and S=E-U; these arithmetic components do not identify a repair mechanism.
Every family's components and every block/world difference remain in the aggregate. Even
the M-exposed cluster family has an adverse mean difference in four of five blocks, so this
batch does not support a simple observed story of buying a consistent cluster benefit with
uniform specialization loss. It also does not prove that such a tradeoff is impossible.

The prior A2 positive pair remains valid selection evidence (+.018568986 J / +.940750
hotspot service), and C01 block 1 is a further positive instance. What weakens is the reason
to replace ordinary U by this fixed 8/8 program on the strength of the initial increment.
Useful ordinary U learning is reinforced. This is not an absence of learning by M, failure
to execute, evidence for a new architecture, or proof that training coverage never matters.
C01 changed both training instances and the evaluation panel relative to A2, so it cannot
attribute the reversal uniquely to training randomness, spatial preferences or panel interaction.
Those are unresolved explanations, not reasons to erase adverse evidence or automatically
purchase more training.

### Complete cost, prior advice and next scientific decision

C01 cost **10 fits, 3.6M training +720k evaluation =4.32M team steps /25.92M UAV action
rows**, 450 updates, 1,012,500 actor and 1,012,500 critic optimizer calls, 45 panels and
1,440 evaluation episodes. Actual scientific walls sum to **22,685.868930 seconds /6.301630h**;
the ten arm walls sum to 22,684.674419 seconds. Sum of native admission-to-exit is
23,650.418796 seconds /6.569561h. First admission through final exit spans
26,772.730281 seconds /7.436870h, including inter-block collection/publication/recovery gaps.
These are different scopes, not a speed comparison. Process user/system CPU sums are
90,701.458210/196.290596 seconds; maximum per-process peak RSS is 1,843,748 KiB with four
torch threads, not summed simultaneous memory. Full engineering, review, consultation,
publication, readback, other-process resource use and peak scratch totals remain unmeasured.

The five native inventories contain **680 files /5,440,071,755 bytes**. Each block has a
verified local mirror and an independent retained copy; the latter alone adds the same
5.440 GB, with the local mirror another copy. Aggregate/report files are additional and
small. Prior A2's two fits and 864k team steps remain separate selection cost, never part
of confirmation n. No sixth fit-pair or new evaluation follows from completing this batch.

The complete prior Pro answer at `ca77013402426ce5254ab260d688b651e3664178`, sections 3–7,
already covers this final-reading branch: preserve the intervals and all blocks, decline
automatic sixth-block or location rescue, and separate zero-margin statistical support from
adoption. I reuse that advice for the fixed result rather than seek a new verdict on the
same rule. This ends the confirmation, not by itself ownership of the broader question.

Current shared background at main `c3fadf6c293f6b794f7e80aa2b66711b1aa60c7d` was read at this
material boundary. B20's separate adverse/uncertain confirmation and declined panel replay
reinforce the need for a next observation to change a concrete investment, but do not supply
C01 replication or its cause. C2's completed sending comparison and S7's still-owned model
question are separate opportunities, not assets to take over. The unowned C1, A3 and D1
planning questions remain distinct and are not automatically selected by C01's outcome.

The next decision is whether any feasible spatial comparison now has enough explanatory
and actionable value to justify its full cost, or to end the current mixed-layout route.
A fixed-policy old/new-panel crossover could separate finite policy-pair and panel patterns;
it would add no training n and would not itself identify a useful data intervention. A
four-center replay asks position sensitivity, not the failed conditional mean. Neither
observation is selected merely to explain away the negative means; changing mixture,
horizon or architecture also needs a new discriminating prediction. This new evidence can
materially change route investment, so a focused Pro follow-up will challenge that decision
under constitution section 5 before choosing a continuation or wider closure. The fixed
C01 result and directly affected shared understanding are ready for independent publication;
no additional experiment has been selected or launched.

## Pro question 2026-09-25 c01-next-spatial-investment

Conversation: reuse the existing Jev-account direction conversation; its address stays in
local operation state. The earlier A2/C01 question is complete and closed. This is a new
route-investment question based on the complete C01 evidence, not a resend or a request to
change the frozen confirmation rule.

Question type: research-route choice and working-explanation update under constitution
sections 2 and 5. C01 is finished. Is there now a feasible spatial/task-distribution
comparison whose explanatory or practical value justifies its cost, or should we end the
current mixed-layout route while retaining ordinary U and the bounded positive instances?
Challenge the reasoning below, including the strongest case for a worthwhile continuation.
Do not manufacture a successor merely because the batch ended or all uncertainty is not resolved.

Standing: all five fresh paired blocks and all ten fits have been read and independently
retained. The complete fixed result is published at
`b35996ba188d31cc01b3a422a47c24b1fde6bce3`. Its material standing and directly affected shared
understanding were published to main at `026e3e6e7904f288a7bdab05471e7e37195028f5`.
No native experiment remains active; no sixth block, new fit or additional evaluation has
been selected. Current owner pause is lifted; there is no newer owner stop. DM scientific
continuity, three-track resource ceiling, existing owners and App-message boundaries remain.

Evidence and current interpretation:

- The original A2 single-pair hotspot M-U gain was +.018568986 J / +.940750 served users
  per step, with 12/32 adverse worlds. Uniform service was approximately zero with 17/32
  adverse worlds, not noninferiority. This positive instance is preserved, not pooled into C01.
- C01 kept N6/c10, 50 users, LOCAL1 and legal actor/critic inputs, ordinary PPO, the actual
  same within-pair initialization, recurrent/update semantics, 360k train steps per arm and
  final45. U uses 16 uniform lanes per update; M substitutes eight cluster lanes, rotating
  by the fixed rule. Nothing about actor information, architecture, horizon or endpoint was
  chosen after outcomes. Hotspot participates only in evaluation. New model seeds are
  263000101..263000105; the same fresh 32-world panel per family is shared across those
  pairs, with hotspot seeds 265020000..265020031. A2 used hotspot 262020000..262020031.
- Five hotspot J differences are -.014721197, +.019314215, -.052880403, -.015865239,
  -.064009839; service differences are +.0079375, +1.4823125, -1.7528125, -1.4954375,
  -4.197750. The prewritten marginal two-sided df4 t95 intervals are J
  -.025632493 [-.067046834,+.015781848] and service -1.191150 [-3.827524015,+1.445224015].
  The required joint positive mean is not established. Both means are adverse and both
  intervals cross zero; neither equivalence nor a certain harmful population effect follows.
  The service interval still includes the approximately one-user reference and substantial loss.
- C01 block 1 is positive in all three family means. Across the five blocks, uniform means
  are -.027514607 J / -1.263750 service and cluster means -.029872854 / -1.472138;
  each endpoint/family has one positive and four negative blocks. Thus a consistent observed
  cluster benefit buying uniform loss is not the pattern of this batch.
- Every one of the ten fits improves its own J/service mean in each family relative to its
  real initialization. Hotspot U/M own means are +.268719420/+13.261900 and
  +.243086928/+12.070750. U has no own-J/service loss on any evaluated world; M has one
  own-J and five own-service exceptions, retained in the block readings. Ordinary U is a
  competent learning comparator. M learned too; its failure to add mean utility is distinct.
- Eligibility, service, quality and height components are read, including local large losses;
  their algebra does not identify an optimization/representation mechanism. A2 to C01
  changed both training instances and evaluation worlds. Neither training randomness nor
  panel dependence has been isolated. n5 and fixed shared worlds do not establish arbitrary
  layout transfer, next-training reliability or iid-normal validity.

My current leaning is to retain U and decline more investment in the same 8/8 replacement
recipe. The initial positive did justify a fixed replication, but the complete result now
weakens its case. Merely widening intervals, preserving possible benefit, or listing
"optimization/capacity/seeds" does not supply a targeted intervention. That is a cost/value
judgment to challenge, not a claim that spatial coverage cannot matter. A consequential
explanatory result can be worthwhile in its own right; it need not promise a performance win.

The strongest concrete low-fit alternative I can presently specify is a retrospective
**old/new hotspot-panel crossover of all six retained policy pairs**, not just the favorable
pair: A2 and all five C01 pairs, U45/M45, on both existing 32-world hotspot panels. A complete
rerendering is 6 pairs x 2 policies x 2 panels x 32 worlds x H500 = **384,000 evaluation team
steps /2.304M UAV rows**, 768 episodes, 24 panels, twelve retained policy/normalizer assets,
zero new fits or optimizer calls. Twelve diagonal panels/192k steps already have native
readings; rerendering those would check replay identity, with twelve off-diagonal panels/192k
steps adding the missing comparisons. Reusing verified diagonal evidence instead could avoid
some repeat evaluation, but requires an explicit prospective semantic/provenance comparison.
No crossover has been selected or executed. Implementation, checkpoint loading, actual
physical-panel identity, review, fresh resource admission, raw retention and reading all cost
work; standalone wall/storage have not been measured. Zero fits is not a zero-cost claim.

If signs follow the pair on both panels, this would weaken a purely panel-specific account
for these policies; if M-U varies systematically with panel within pairs, it would support
finite policy/panel interaction. Neither pattern estimates the population variance of
training or diagnoses a causal optimizer/coverage defect. Both panels and all policies are
already result-exposed; this is new exploratory explanation, not a new confirmation n or a
rescue of C01. Which resulting distinction would materially improve our scientific answer or
change a warranted next comparison, and is that gain worth even this smaller cost? If no
branch does, recommend declining it. Do not assume the separate B20 panel-replay decision
settles this spatial question.

The prior four-center A2-only alternative (0 fits/128k evaluation team steps) tests the
location sensitivity of one already selected pair, not the C01 program mean. New mixture
ratios, longer horizons, curriculum or representation changes need a distinct, evidence-linked
intermediate prediction and native consequence; the current loss does not select one. If
a concrete alternative is stronger than crossover or closure, describe its ordinary matched
comparator, information rights, discrimination, likely scope and dominant work. No fixed
number of proposals, architecture, exhaustive diagnostic campaign or new learning is owed.

Relevant project context: B20's roster comparison, C2's sending decisions and S7's still-owned
approach-model question have different estimands; their results are not C01 replications or
its cause, and this task does not take over those owners. The current plan has unowned C1
finite-model decision value, A3 genuine capability composition and D1 partner composition.
They show that closing one recipe need not end DM responsibility, but they are not selected
by this result. This question is a focused investment choice for the present spatial work,
not a project-wide portfolio review. A materially justified nearby pivot can be proposed;
do not use a reserve label or an unspecified future discovery to postpone a decision.

Cost and exposure: completed C01 used 10 fits, 3.6M train +720k evaluation =4.32M team steps,
450 updates and 1,012,500 calls of each optimizer. Actual scientific wall sum is 6.301630h,
admission-to-exit sum 6.569561h, max single-process RSS 1,843,748 KiB, four torch threads.
680 native files/5,440,071,755 bytes have local and independent retained copies; full
engineering/review/consultation/readback and peak scratch totals are unmeasured. A2's two
fits/864k team steps remain separate selection exposure. Prospective selected experiment
cost is currently zero because none is chosen; candidate crossover/four-center costs above
are discussion estimates, not accepted operations or entitlements.

Context sources (source_sha means this question's full published commit, supplied in the
actual message; other revisions below are immutable):

- Current governance: `docs/project/OPERATING_CONSTITUTION.md` sections 1-5, 7-8 at source_sha.
  Ordinary choices are delegated to this direct DM; Pro advises, does not allocate compute
  or add approval requirements. Frozen C01 is not reopened by current methods.
- Current methods: `.agents/skills/hmasd-scientific-tools/SKILL.md` at source_sha, Update the
  working explanation, Use and revise shared understanding, Comparators and MARL information,
  Statistics, Cost and exposure, Pro. Use these to separate explanation/value/precision;
  there is no mandatory toy test, tuned-headroom gate or duty to rescue the package.
- Current shared understanding and opportunity cost: `docs/research/RESEARCH.md` at
  `026e3e6e7904f288a7bdab05471e7e37195028f5`, section 3's ordinary learning/roster/A2-C01
  passages, own Active row, Current research plan question map, and running/ownership scope.
  This is revisable understanding, not governance or independent evidence for our mechanism.
- Fixed contract: `docs/research/candidates/spatial_demand_generalization/CLAIM_layout_coverage_conditional_mean_20260924.md`
  at `b6c6836a7221a31429b6b4665d077b9097dd8e10`, original claim/batch/estimand/cost and Adoption.
  Read its appended complete result at `b35996ba188d31cc01b3a422a47c24b1fde6bce3`.
- Complete C01: this NOTES at `b35996ba188d31cc01b3a422a47c24b1fde6bce3`, "C01 complete:
  joint positive mean not established" and the five complete block entries as needed for
  adverse cases; `runs/spatial_demand_generalization/c01_five_block_confirmation_20260925/summary.json`
  (`units`, `interval`, `by_family`, `primary_hotspot`, fixed joint decision) and `reading.json`
  at the same revision. The aggregate retains every block/world result; read sufficient
  supporting and contrary fields rather than only the decision boolean.
- A2 selection and assets: this NOTES's "A2 complete: modest held-out gain and heterogeneous
  local costs" and `runs/spatial_demand_generalization/s1_spatial_coverage_a2_s260925101/summary.json`
  at `3453c67f1c9eb748300a4dca9746bf88e52119b9`. Native NPZ/checkpoints are retained at paths
  recorded in NOTES but are not GitHub-readable; I verified them, you must not claim that you did.
- Prior advice to reuse, not repeat: this NOTES at
  `ca77013402426ce5254ab260d688b651e3664178`, Answer under "Pro question 2026-09-24
  a2-replication-or-spatial-dependence", especially sections 3-7 on C01 scope, final reading, four-center alternative and
  no automatic extension. Its fixed-rule advice still applies; the five new results now
  motivate this focused investment follow-up.
- Only if a feasibility or causal premise requires source inspection: accepted C01
  `9e44adde3d54fcd0363a2ebdbc1468494141c27b`,
  `experiments/candidates/spatial_demand_generalization/c01/runner.py` and reused
  `experiments/candidates/spatial_demand_generalization/a2/runner.py` / `adapter.py`.
  A2 accepted source is `d22b608e8d063ceac5c944426bd35a2289c5ebf6`; do not infer a source
  equivalence or replay guarantee from identical labels alone.

Constraints: advice only, no training/evaluation, experiment implementation or cross-task
messages. Write only the empty `### Answer` under this unique heading in
`docs/research/candidates/spatial_demand_generalization/NOTES.md` on branch
`codex/spatial-demand-generalization-a2`. Read the pinned question, then fetch the latest
target file for writing and use its actual blob SHA. Preserve the question and all other
bytes; stop on overlapping edits. Report the actual commit on success. On write failure,
return the complete answer in chat, not just a receipt, SHA or link.

Return a focused recommendation with MATERIAL_DISSENT yes/no and the strongest objection to
my current leaning. State what the new evidence strengthens, weakens and leaves unresolved;
whether crossover, a specific alternative or ending this route is now the useful next choice,
and why its distinct possible observations matter. For any proposed intervention, name an
intermediate prediction, native outcome, simplest competent comparator, exposure and fit/
non-fit costs; retain assumptions and uncertain cost honestly. Distinguish ending this
recipe, ending current spatial investment and becoming idle. No positive result, new idea
quota, rule revision or automatic confirmation is requested. Cite sources actually used for
consequential claims and state unread decision-critical gaps without pretending verification.

### Answer

Saved from chat on 2026-09-25 after `deliver` returned `NOT_DELIVERED` and the latest
branch/file was verified to remain at the pinned empty Answer. The complete collected
text follows verbatim; browser-extracted math/table layout and source-chip text are preserved.
No GitHub write was attempted by Pro, as its opening statement explains.

本轮未完成 GitHub 写回。 GitHub 读取正常，指定的 ### Answer 仍为空；但我未完成整文件替换载荷中“其他字节保持不变”的校验，因此没有发出写请求，也没有产生提交。这不是 GitHub 拒绝了写入。以下是完整答复。

Answer

MATERIAL_DISSENT: no。

建议保留普通 U，结束当前 8/8 混合布局配方的追加训练，同时结束当前空间路线的新增实验投入。 不选择六对策略的旧／新 hotspot 面板交叉回放，也不选择 A2 单对的四中心观察；不以改变比例、延长训练或增加表示机制作为默认后继。

决定性理由不是“确认没有通过，所以必须停止”，而是：新证据同时削弱了该配方的增量用途和一个明确的专门化取舍解释；已有分量没有选出值得修复的具体环节，而候选回放的主要新增信息仍是两个已曝光有限面板之间的表现归属。 这个信息并非无价值，但我认为目前不足以购买相应实施、核验、执行和完整阅读。

对你当前倾向的最强反对意见是：不能把“能否立即选出下一项性能干预”当成解释研究的唯一价值标准。交叉回放确实能够产生独立的、有限范围的科学答案，而且复用既有对角证据可能把新增评价降到 192k 团队步。不能仅因它不增加训练重复、不识别优化器机制，就把它说成没有意义。下面的停止建议是在承认这个最强理由后，仍对其当前边际解释价值作出的判断，不是给所有诊断研究设新门槛。

一、固定结果应保留为“均值不利、精度有限、联合正主张未建立”

C01 原规则检验的是：在固定的新 hotspot 面板上，两个完整训练程序的训练区组平均差，其 J 与服务的边际双侧 95% t 区间下界是否都严格大于零。它不是要求五块全正，也不是按正负块数多数表决。原计划、Adoption 和最后结果没有提供改写这个规则的理由。

五个主项必须一起保留；服务单位为用户／步，不利世界指 J 或服务至少一项下降：

区组／模型种子	Hotspot M−U：J	Hotspot M−U：服务	Hotspot 不利世界
0／263000101	−0.014721197	+0.0079375	22／32
1／263000102	+0.019314215	+1.4823125	9／32
2／263000103	−0.052880403	−1.7528125	31／32
3／263000104	−0.015865239	−1.4954375	23／32
4／263000105	−0.064009839	−4.1977500	27／32

这些是同一固定面板上的五个训练区组差，不是 160 个训练重复；不利世界数也不是未来训练的失败概率。

完整的主、次要均值和预写区间为：

家族	平均 J 差及 t95 区间	平均服务差及 t95 区间
Hotspot，主项	−0.025632493；[−0.067046834，+0.015781848]	−1.191150；[−3.827524015，+1.445224015]
Uniform，次要	−0.027514607；[−0.068822823，+0.013793609]	−1.263750；[−3.084825853，+0.557325853]
Cluster，次要	−0.029872854；[−0.085282714，+0.025537006]	−1.472138；[−5.062347136，+2.118072136]

我按原始五块主项复算了均值、样本标准差和 df4 t 区间，得到与发布汇总一致的结果。两个主项下界均未过零，联合主张未建立；两个上界也都不是负数，因此不能把它升级为已确认的有害总体效应。服务区间仍包含约一人增益，也包含较大的损失。

“尚未排除有益效应”与“值得继续购买同一比较”是不同判断。 当前不应把区间跨零写成等价或无效，也不应反过来把区间包含正值写成追加训练的依据。t 区间的解释仍依赖其工作模型；小样本不能自行验证近似正态性，置信区间也不是下一次训练获益的预测区间。这里沿用原分析，而不以新统计方法重新裁定 C01。外部方法核对仅用于确认这些统计解释，不提供任何新的 HMASD 实验事实。
NIST
+1

二、这批数据已经改变了什么，而不只是“仍有不确定性”

加强的是普通 U 的有限学习用途。 在 C01 的 hotspot 上，跨五块的共同初始化、U45、M45 平均服务分别为 12.512563、25.774463、24.583313；U／M 自身服务增量为 +13.261900／+12.070750，J 自身增量为 +0.268719420／+0.243086928。十次训练在三个家族的自身 J、服务均值都改善。M 学习了，只是未建立超出 U 的平均增量；这不是没有运行真实学习，也不是 M 整体没有用途。

削弱的是当前 8/8 替换程序作为普通 U 默认升级的理由。 Uniform 和 cluster 的两个端点都分别是一正四负，而且正的是同一个区组 1。因而，这批数据没有呈现“稳定获得 cluster 的专门化收益，代价是 uniform 损失”的简单模式。尤其是 cluster 本来已经进入 M 的训练，不能在它也平均不利时，仍把失败概括为只发生在未见 hotspot 的迁移问题。这个观察不证明所有专门化取舍不存在，但确实让当前这一解释失去支持。

这里有一项值得收紧的解释，而不需要新增评价：

A2 到 C01 的反转尚未分离训练实例与面板变化；但 C01 内部已经在完全相同的评价面板上出现训练配对之间的正负差异。

因此，“尚未分离 A2→C01 的反转来源”不等于“目前没有任何证据区分固定面板下的策略配对差异”。区组 1 为正、其他四块的 J 为负，不需要换面板才能发生。再加上三家族的区组方向大体共同变化，一个只把问题定位为新 hotspot 面板特别不利的解释，已经不足以概括全部观察。 这仍然没有分离初始化、训练世界、采样和优化各自的贡献，更不能命名为已诊断的“优化器缺陷”。

正面证据不能因停止而被删除。A2 的 +0.018568986 J／+0.940750 服务仍是一个有效的有限正例；C01 区组 1 则在新面板上给出另一正例。但区组 1 的正 hotspot 均值仍伴随九个不利世界，其中世界 265020000 少服务 7.196 人／步；区组 4 在世界 265020011 的配对损失达到 14.314 人／步。正例不是虚假结果，正均值也不是局部无损。不能选择性保留正区组作为今后的默认权重，或者选择性保留负区组作为总体有害证明。

三、原生分量没有选出一个应当立即修复的环节

以 U
e
	​

 表示“具资格但未服务人数”，避免与训练臂 U 混淆。C01 hotspot 的平均差为：

ΔE=−1.3410125,ΔU
e
	​

=−0.1498625,ΔS=ΔE−ΔU
e
	​

=−1.191150.

这与 A2 的“资格增加，但其中一部分没有转成服务”并不是同一个总体分量模式。A2 中资格增加 +2.264125，同时具资格未服务增加 +1.323375；C01 中资格平均减少，未服务资格的减少远不足以补偿。不能沿用 A2 的分量描述，直接宣布 C01 的核心问题仍是“把新增资格转成服务”。

同样，按原生公式作描述性代数分解：

ΔJ=0.7ΔC+0.3ΔQ−ΔP=−0.016676100−0.001553630−0.007402763=−0.025632493.

高度代价增加是一个不利分量，但覆盖和质量的加权小计本身也为负，约 −0.018229730。把高度罚从账面上扣掉，不等于存在一个保持其他后果不变、能够回收这部分损失的物理或训练干预。S1 的这个项仍然是高度罚，不是实测电池能耗或安全风险。

区组层面的反例进一步限制单一修复解释。区组 2 的 hotspot 资格增加约 +0.924563，服务却减少 −1.752813，具资格未服务增加 +2.677375；区组 3 的高度罚已经降低、质量已经提高，服务和 J 仍然下降。于是，“更多资格”“更低高度”都不是一条已经得到一致支持、只差实现的修复链。它们可以参与未来假说，但本批没有选中其中一条。

这不是要求探索前必须证明机制或最优性。当前方法允许合理启发式和小规模探索；我的判断只是：现有证据尚未让某个具体数据或训练改动，比其他可想象的改动更值得购买。 不能用候选名称代替这一缺失的理由。

四、六对旧／新面板交叉回放的最强价值，以及为什么本次仍不选择

交叉回放能回答一个真实但有限的问题。令

d
p,w
	​

=
J(M
p
	​

,w)−J(U
p
	​

,w)
	​


表示固定策略配对 p 在面板 w 上的差，服务同理。补齐旧、新面板后，可以直接读取同一配对的

δ
p
	​

=d
p,new
	​

−d
p,old
	​

.

现在 A2 的旧面板读数与 C01 的新面板均值之间，J 相差约 −0.044201479，服务相差 −2.131900。这是跨训练实例、跨面板的观察差，不是训练因素或面板因素的因果份额。 补齐缺失格，确实能够使这张有限表的解释更完整。

最值得考虑的结果分支如下。这里没有预测这些尚未执行的结果会出现。

可能观察	真正增加的认识	对当前投入判断的影响
A2、区组 1 在两面板均有利，其他配对大体仍不利	削弱“仅更换面板就解释历史反转”的说法；支持这些固定策略配对的差异跨两面板保留	使解释更具体，但同面板配对差异已被 C01 观察到；没有指出新的训练干预
同一批配对普遍在旧面板更有利，在新面板更不利，甚至反号	表明两个有限面板对 M−U 差具有实质影响，不能把 A2→C01 全归给训练实例	这是最强的继续理由；但旧／新只是同一生成器的两组已曝光抽样，不是已定义的、可在部署前识别的两类空间条件
不同配对的面板响应不同，或者 J、服务响应不同	得到更细的有限交互与原生取舍	不自动选择混合比例、训练时域、中心分布或表示改动，也不改变 C01 原判读

这些分支来自题面拟议设计及上述差值定义，不是新的经验结果。符号是否保留也不能独自代表敏感性：符号不变时，幅度仍可能明显改变；所有配对同方向、近似同量变化，与只有少数配对大幅变化，也不应合并为同一种解释。

第二种分支是我认为最可能实质改变历史解释、因而最值得认真对待的反对停止理由。 我不把它说成“即使出现也没有信息”。但它仍主要告诉我们：这六对已曝光策略对两组有限抽样的平均差不同。它没有把差异绑定到一个独立定义的需求属性，也不能把其中较有利的一组重新命名为目标总体。若据此再挑世界、拟合分组或寻找几何解释，那是额外的结果后探索，不能混进本次 crossover 的既定价值里。

因此，我仍不选择它。现有结果已经足以形成有内容的科学答案：普通 U 在这些条件下学到显著自身用途；8/8 程序的初始增量没有建立新面板上的正条件均值；配对差异在同一面板、多个家族上已存在。 为进一步确定历史变化在两个有限面板上的分布位置，再投入一次资产加载、执行和完整原生阅读，我认为当前不相称。

这是一项可争论的价值判断，不是“所有结果分支都毫无意义”的断言，也不是“解释研究必须保证性能改善”的规则。它不依赖 B20 已经作出的回放选择；本次理由来自 C01 自身的五块、三家族和原生分量。

五、成本比较应承认复用可能性，但不能把它写成现成的免费执行

题面提供的成本算术成立：

候选	新 fits／优化更新	新评价团队步	回合数	当前状态
六对策略、两个面板全部重新执行	0／0	384,000	768	未选择
复用全部已验证对角证据，只执行缺失格	0／0	192,000	384	依赖明确的语义与来源一致性比较；未选择
A2 单对、四个新中心	0／0	128,000	256	未选择
本答复建议：结束当前新增实验投入	0／0	0	0	方向建议，不是已完成的 DM 决定

完整 crossover 的 UAV 行动行为 2.304M；仅缺失格为 1.152M。前两行包含的是同一张最终交叉表，但新增执行量不同。既有对角数据的历史取得成本仍保留，不能把复用写成这些数据从未花费过资源。

192k 是可以讨论的较小执行范围，不是本轮已经验证可直接执行的方案。 真正复用需确认旧证据与新评价在策略／normalizer 身份、执行动作法则、循环状态重置、H500 终止、物理初态以及 J／服务计算上的对应关系。相同标签、同一 seed 名称，或“代码主要复用”都不能代替这些对应。若需要额外对角回放来验证加载或执行路径，它们必须计入新增成本，而不是隐含在 192k 中。本轮没有加载这些二进制资产，也没有建立回放保证。

既有 C01 的实际科学过程墙钟合计为 6.301630 小时，准入至退出合计 6.569561 小时，首次准入到最终退出跨度 7.436870 小时；三个数是不同口径。十个 fits、4.32M 团队步、680 个原生文件及 5,440,071,755 字节是已经发生的成本，工程、审查、咨询、读取和峰值临时存储并没有被完整计量。不能把包含训练的大批次墙钟按评价步数比例缩放，冒充 standalone crossover 的实测费用。

停止也不意味着收尾、保存和更新解释没有工作成本。我的建议是不再购买新的结果性实验，不是声称研究收尾免费。已经投入六个多小时既不是必须继续的理由，也不是必须停止的理由；下一项观察要凭新增价值，而不是凭沉没成本或空闲名额成立。

六、四中心、比例和训练时域变化目前都没有成为更强的替代项

四中心方案检验的是两份 A2 终点对指定相对几何变化的敏感性。它不代表五个 C01 训练区组，也不能替代新训练下的程序差。此前建议还指出：四个新中心没有原来的 (0.5,0.5)，所以把新中心负结果与旧 A2 正结果直接比较，会同时改变中心和世界批次；只有同一新 base world 内的中心比较才隔离了该中心变化。现在没有新的证据使这一项成为当前空间投资的首选。

改变混合比例、延长训练、调整 curriculum 或更换表示，不是被禁止，也不需要先取得理论证明。但本次没有观察到一条足够明确的中间预测，例如某项可识别的学习失配，在一个具体改动后应减少，并伴随原生服务／J 的改善。只说“混合任务可能需要更多训练”“减少 cluster 或许保留 uniform”“新表示可能更稳”，还不足以在这些选择之间作出有依据的选择。尤其是延长训练会改变预算问题，改比例会改变程序，不能把它们称为原 C01 的简单延续。

普通 U 的用途因此应保留为工作参照，但不能被提升为“充分调优”“空间问题已饱和”或“任何混合训练都无用”的认证。当前共享背景中的 LOCAL1 经验使这个参照有具体意义；B20、C2 和 S7 的其他结果则只提供各自范围内的经验，不能作为 C01 的复制样本或机制证据。

七、把三个“结束”分开，并现在作出明确选择

结束配方。 不再为相同的 8/8 替换程序购买第六区组、另一轮确认、早期端点救援或无新预测的调参。C01 原判读保持不变，A2 和区组 1 的正例也保持不变。这与此前已交付建议的固定终局读取和不自动延长分支一致。

结束当前空间投入。 本次不把停止训练包装成仍持续购买 crossover、四中心或其他常驻诊断。我建议在现有 NOTES／RESEARCH 中将“当前无值得选定的新增空间实验、当前混合路线投入结束”写清楚，同时保留问题、全部正反结果、来源和可恢复资产。它是当前投资状态，不是空间任务分布研究的科学否定。

DM 责任不等于必须维持一个正在运行的空间实验。 当前计划中的 C1、A3、D1 是独立问题，但它们不被 C01 的结果自动选中，也不能用它们的 reserve 标签或某个未具体化的未来发现来推迟本次停止决定。本答复不重排项目组合、不接管已有负责人，也不替 DM 宣布已经承接了新任务。宪章允许在没有值得选择的工作时释放运行资源；不欠阳性，不欠无限后继，更不欠把三个名额占满。

若 DM 采纳，当前科学结论可以压缩为：

在固定 S1／N6／c10、LOCAL1、360k 训练预算与 final45 条件下，普通 uniform 训练在所评布局上具有明显自身学习用途。8/8 uniform／cluster 替换程序保留了探索正例，但五个新配对在新固定 hotspot 面板上未建立联合正条件均值，平均方向不利且区间仍宽；uniform 和已见 cluster 的增量均值也不利。现有证据没有识别一个值得针对性修复的环节，旧／新面板交叉回放的额外解释价值不足以支持当前投入，因此结束这条混合路线的新增实验，保留 U、正例、反例和尚未解决的归因边界。

这不是把未知原因判成无效，也不是因为一个批次完成就结束责任；它是对已经获得的答案与尚可购买的信息作出的明确取舍。

八、读取范围与剩余缺口

本答复依据的是新题固定提交 2afd0915dffe00c3b66dfecc5c59d959c394d3f5 的完整问题、指定宪章章节和科学方法；共享背景使用指定的 026e3e6e7904f288a7bdab05471e7e37195028f5，包括普通学习／A2–C01 段、当前方向行、问题地图及负责人范围，没有用移动分支的新结果替换科学输入。

固定合同与 Adoption 使用 b6c6836a7221a31429b6b4665d077b9097dd8e10；C01 完成条目、追加结果、聚合 summary.json 的分析单位、区间、家族／区组值、原生分量及支持／不利世界字段，以及完整 reading.json 使用 b35996ba188d31cc01b3a422a47c24b1fde6bce3。A2 使用指定 3453c67f1c9eb748300a4dca9746bf88e52119b9 的完成记录和原始汇总；既有建议重新读取了 ca77013402426ce5254ab260d688b651e3664178 的有关完整章节，不以旧聊天结论代替这些来源。

没有读取 Git 外的 native NPZ、训练流和 checkpoint 二进制，也没有亲自重做 720k 原生评价转移的核验。 原生完整性与独立保全属于所读 DM 验收记录；本轮独立计算只覆盖上述五块主统计和明确展示的代数。也没有重新审查 C01／A2 的完整执行源码或验证二者可逐字节回放等价，因此我没有把 192k 复用方案当作已经准备好的执行承诺。题面将这种源码检查列为存在相关可行性争议时的条件读取；本次停止建议不依赖一个未经验证的回放保证。

没有缺失的指定关键文本阻止上述方向建议。真正未获得的是尚未执行的交叉结果、它的 standalone 墙钟／存储、以及训练变化与面板变化的更细归因；这些不能用别的方向、文献类比或记忆补全。

最终建议：MATERIAL_DISSENT: no。保留 U 和全部有界正反证据，结束当前 8/8 配方及当前空间路线的新增实验投入；不附带交叉回放、移中心救援或自动后继。

## 2026-09-25 — decline panel replay and end current spatial mixing investment

**DM decision.** I adopt the complete advice's recommendation to retain ordinary U and end
new result-bearing investment in the current spatial mixing route. C01's fixed confirmation
is already complete; I also decline the proposed old/new-panel crossover, the A2-only
four-center observation and a new mixture/horizon/representation search. The direction's
current investment state becomes **archived**, with no selected successor, pending fit,
evaluation or Pro answer. This ends the present route after assessing its concrete remaining
options, not the scientific possibility of useful task-distribution learning. It does not
convert the adverse point means into confirmed harm, equivalence or a universal negative.

### Complete answer, delivery reconciliation and source limits

The new question was published at `2afd0915dffe00c3b66dfecc5c59d959c394d3f5`, key
`hmasd:2ccc38bf565731d6bcc1e2da74b734b26413ec88dffe2f75d7ae580c86669f4f`.
An initial composer-load timeout happened before any Send. A read-only check of the same
conversation found its composer ready, no login/challenge/page error and only the two old
turns. The original key, exact text and attachment were then used; one Send was accepted
with observed `6 Pro`, `send_effect=sent` and attachment present. Nothing was resent after
acceptance, and the prior A2 consultation remained closed.

The deterministic generation-30 observer collected the complete 7,954-character visible
answer. Its trimmed-text SHA256 is
`b243c62e8c42ee4c15fee0545855d962810b798e932af04fdd0c3af68db1383a`;
the 19,131-byte UTF-8 fallback file, including its terminal newline, has SHA256
`472c6cf2182a11b38ed517d22adde466d130117c5e94508f18b688948092cd51`.
I read the entire answer. `deliver` returned `NOT_DELIVERED`, with no answer-writing commit;
the two hashes classified by the observer as receipts were the question and shared-context
inputs, not delivery commits. Pro explicitly says it made no write request because it did
not finish checking preservation of the rest of the file. This was not a GitHub rejection.

Immediately before saving, the remote branch still resolved to the pinned question commit,
the unique Answer was empty, and both owned authoring/publication copies exactly matched
that file. I therefore saved the complete collected text verbatim above, marked **saved
from chat**, preserving the question and all previous bytes. No answer was overwritten or
duplicated. The READY event `61b24aa7cde1415ab8970094` from wake
`d06bbd86-d180-4a5d-899a-ce9cf6194aa2` was consumed and the same controller reconciled to
generation **31**; every registered experiment and Pro observation is terminal. The browser
workflow closed only its owned tab. No worker, accepted request or other task was restarted.

The adviser names the pinned question, constitution/methods, main background, original
CLAIM/Adoption, full C01 aggregate and reading, A2 evidence and prior advice as its inputs.
It explicitly did not read Git-external binaries or certify replay equivalence. Those limits
are compatible with this investment judgment; no feasibility guarantee for a 192k replay is
being adopted. The extracted answer preserves its math/table display and the unresolved
external citation chip text (`NIST`, `+1`). I do not claim to have verified those external
citations or use them as new evidence: the statistical reading remains the frozen local rule
and the already independently checked five-block arithmetic. Advice is not another experiment.

### What I adopt, refine and leave unresolved

I adopt **MATERIAL_DISSENT: no** as the adviser's position, not as a scientific acceptance
test. All five pairs, both primary intervals, secondary families, own learning and local
losses stay as published. I checked the adviser's additional concrete examples against the
retained aggregate: block 1 hotspot world 265020000 has service M-U -7.196 despite the
positive block mean; block 4 world 265020011 is -14.314. Block 2 increases mean eligibility
by +.9245625 but increases eligible-unserved by +2.677375, leaving service -1.7528125.
Block 3 reduces height penalty by .003683035 and improves quality by .004626167, yet J and
service remain adverse. No single "more eligibility" or "lower height" repair follows from
these components. This check used saved JSON, with zero new policy/environment calls.

One useful refinement already follows from C01, without buying another panel: at each
fixed family panel, the five paired J differences have signs [-,+,-,-,-]. Pair 1 is positive
across all three families; the other four are negative across all three. Thus the evidence
already exhibits policy-pair differences while the evaluation panel is held fixed. This
does **not** attribute A2-to-C01's changed mean to training rather than panel, identify which
training randomness matters, establish cross-family independence or prove an optimizer defect.
It does prevent treating the situation as if no within-panel variation were observed.

The average component identities also constrain an inherited explanation. C01 hotspot has
eligibility -1.3410125 and eligible-unserved -.1498625, yielding service -1.191150; A2's
positive-eligibility/partly-unconverted story is not this batch's mean pattern. The weighted
coverage/quality subtotal is -.018229729983 before the additional height penalty
.007402762799. This is descriptive algebra, not an intervention holding all other physical
consequences fixed. It neither selects a height controller nor implies measured energy loss.

I adopt the strongest objection to stopping: finite-panel explanation can be valuable in
its own right and need not first promise a performance repair. Full crossover costs 384k
evaluation team steps; reuse of valid diagonals could reduce new execution to 192k, plus
any needed replay checks. A systematic old/new-panel shift would materially refine the
historical account, even if it added no training n. Sign retention would not imply magnitude
invariance. I therefore reject the stronger dismissal that crossover has no information or
that a diagnostic must select a new performance intervention to be legitimate.

I nevertheless decline it here. The six-policy-pair/two-exposed-panel table would localize
finite historical differences, but neither bank is an independently defined deployment
subpopulation. C01 already provides the conditional-program result, own learning and
within-panel pair variation in three families. Completing that finite table currently adds
less to this answer than its loading/semantic comparison, execution, storage and full reading
would cost. Retrospectively mining a geometry subgroup would be further exploration, not
included free in crossover's stated value. This is a scoped, contestable marginal-value
judgment. It is not a theorem against replay, a claim that every possible branch is useless,
or an inference from B20's separate decision.

Four-center A2-only evaluation asks the location sensitivity of a selected pair and would
not answer the five-pair program question. Generic ratio, duration or architecture changes
alter the program again without a currently preferred concrete conjecture among them.
Their lack of selection is not a prohibition on heuristic exploration or a requirement to
identify a causal component before learning. No positive result or exhaustive rescue search
is owed, and the existing positive A2/block-1 examples remain scientifically useful.

### Current structural background and question continuity

Before publishing this decision I refreshed main and read owner update
`2e2becaae8d376908d74364dca7e4713bdcb4a2a`: RESEARCH's **Mathematics, information and game
structure** background, scientific-tools' **Mathematics, conjectures and experiments**, and
the direct-DM body's matching paragraph. This naturally sharpens the present judgment;
it does not alter the accepted question or require another Send. The prior answer's caveat
against making diagnostics or a proved repair chain prerequisites remains applicable.

For this comparison, actor information, legal policy class, partner count and physical
capacity were fixed; the intervention changes the finite training-data distribution under
a fixed budget. Writing the resulting policies as A(D_U,r_b) and A(D_M,r_b), C01 measures
their native J/service difference on the same finite evaluation panel. The common r_b label
does not assert identical consumed random draws along different trajectories. The observed
result cannot identify an information ceiling or policy-class approximation gap. There is
no need to solve those unknown ideal values before considering an experiment. Crossover
would vary the evaluation panel at fixed learned policies, a distinct finite object; its
value/cost judgment above concerns that object, not proof of a generalization theorem.

I apply the update's positive permission as well as its limits: a concrete single-agent,
simple-game or empirical conjecture could justify a small complete MARL comparison with
the unproved coupling stated. Strict proof, positive toys, exact headroom, one-step
counterfactuals and exact suffixes are not entry gates here. None is being required as a
condition for selecting a new data-distribution experiment. At this boundary the specific
remaining proposals have been considered and not chosen on their own marginal value; I
have not inferred that all possible spatial conjectures are exhausted or infeasible.

The refreshed question map still leaves C1 finite-model decision value, A3 actual capability
composition and D1 partner composition as materially different unowned possibilities. They
change uncertainty in decisions, physical composition or partner coupling respectively,
rather than merely repeat this layout-mixture comparison. C01 neither selects them nor
supplies their mechanism, comparator or price. I do not register an unspecified pivot to
keep a runtime slot occupied, nor take over S7 or another lead's accepted work. Ending this
route is a present scientific investment decision; the records and revisable question stay
recoverable, and no Root/owner approval gate or indefinite external wait is added.

Additional scientific execution for this consultation/closure is **0 fits, 0 policy calls,
0 training/evaluation steps**. Reading, transport and publication are real non-fit work whose
total wall was not separately measured. All original A2/C01 costs and retained assets remain.
The directly affected shared interpretation, own standing, plan and routing are updated in
the normal independent main publication; no App report/ACK/forwarding is sent.

### Concurrent project replan read before main publication

The next refresh found main `da8890fc3f6d9e714eaab9c9c472862db0af0fd3`, replacing and
archiving the earlier project plan while leaving this DM's actual spatial decision intact.
I read that change. The preceding C1/A3/D1 map assessment refers specifically to the
`2e2becaae8d376908d74364dca7e4713bdcb4a2a` snapshot; D1 is no longer an unassigned current
opportunity in the new plan. Root now assigns a separate third DM a fixed ordinary-policy
composition question, with a proposed 3x3 B20-F matrix (0 fits/144k evaluation team steps),
while C1 remains an independent reserve and capability/churn questions are no longer an
ordered activation queue. This does not supply a spatial-mixture repair or transfer another
lead's comparison to this task. Its shared role-quality/interaction question is distinct
from our fixed-N training-layout contrast. The present closure and frozen C01 reading stand;
no new question, experiment or takeover is selected here. Main publication preserves the
new project plan and its historical archive, updating only this direction's actual result,
standing, routing and directly affected spatial interpretation.
