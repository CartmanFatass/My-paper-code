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
