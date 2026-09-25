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
