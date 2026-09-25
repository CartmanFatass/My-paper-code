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
